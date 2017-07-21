# -*- coding: utf-8 -*-
from datetime import timedelta
import logging
import re

from bs4 import NavigableString, Tag
import six

from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitles import Cue, CueText

logger = logging.getLogger(__name__)

#: Parser state
INDEX, TIMINGS, TEXT = range(3)

#: Index parsing regex
index_re = re.compile(r'(?P<index>\d+)')

#: Timing parsing regex
timing_re = re.compile(r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2}),(?P<millisecond>\d{3})')


class SubripReadError(Exception):
    """Exception raised on reading error."""
    pass


class SubripWriteError(Exception):
    """Exception raised on writing error."""
    pass


def read_timing(timing):
    """Read a timing string as a :class:`datetime.timedelta`.
    
    :param str timing: the timing string.
    :return: the timing as timedelta.
    :rtype: :class:`datetime.timedelta`
    :raise: :class:`SubripReadError` if the timing is not in the expected format.
    
    """
    match = timing_re.match(timing)
    if not match:
        raise SubripReadError('Failed to parse timing %r' % timing)

    return timedelta(hours=int(match.group('hour')), minutes=int(match.group('minute')),
                     seconds=int(match.group('second')), milliseconds=int(match.group('millisecond')))


def write_timing(timing):
    """Write a timedelta timing as str.
    
    :param datetime.timedelta timing: the timedelta timing.
    :return: the timing as str.
    :rtype: str
    :raise: :class:`SubripWriteError` if the timing exceeds the maximum possible value.
    
    """
    if timing > timedelta(hours=99, minutes=59, seconds=59, milliseconds=999):
        raise SubripWriteError('Maximum value for timing exceeded')

    seconds = timing.total_seconds()

    return '%02d:%02d:%02d,%03d' % (seconds // 3600, (seconds % 3600) // 60,
                                    seconds % 60,  timing.microseconds // 1000)


def parse_texts(elements):
    """Recursively generate :class:`~subliminal.subtitles.CueText` from an iterable of
    :class:`~bs4.Tag` or :class:`~bs4.NavigableString`.

    :param list elements: the elements to parse.
    :return: a list of :class:`~subliminal.subtitles.CueText`.
    :rtype: list

    """
    texts = []
    for element in elements:
        if isinstance(element, Tag):
            # convert tag name to css styles
            styles = {}
            if element.name == 'b':
                styles['font-weight'] = 'bold'
            elif element.name == 'i':
                styles['font-style'] = 'italic'
            elif element.name == 'u':
                styles['text-decoration'] = 'underline'
            elif element.name == 'font':
                if 'color' in element.attrs:
                    styles['font-color'] = element.attrs['color']
                if 'size' in element.attrs:
                    styles['font-size'] = element.attrs['size']

            # check for successful tag name parsing
            if not styles:
                raise ValueError('Unknown tag %r' % element.name)

            # add the cue text with its children and styles
            texts.append(CueText(parse_texts(element.children), styles=styles))
        elif isinstance(element, NavigableString):
            # add the string as str
            texts.append(six.text_type(element))
        else:
            raise ValueError('Unknown element %r' % element)

    return texts


def read_text(text):
    """Read a SubRip-formated text as :class:`~subliminal.subtitles.CueText`"""
    soup = ParserBeautifulSoup(text.strip(), ['lxml', 'html.parser'])
    texts = parse_texts(soup.children)
    if not texts:
        raise SubripReadError('Cue has no text')

    return CueText(texts)


def read_cue(stream):
    """Generate Cues from a text stream.
    
    1
    00:01:43,438 --> 00:01:47,150
    Something is coming.
    Something hungry for blood.
    
    {index}                            starts at 1
    {start_time} --> {end_time}        hours:minutes:seconds,milliseconds
    {lines}                            with possible tags: <i>, <b>, <u>, <font color="ffffff"> and <font size=16>
    
    2 blank lines separate cues.

    :param stream: the text stream.
    :return: the parsed cue.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Cue`]

    """
    state = INDEX
    text = ''
    start_time = end_time = timedelta()
    previous_index = 0

    for line in stream:
        line = line.strip()

        if state == INDEX:
            # skip blank lines
            if not line:
                continue

            # parse index
            match = index_re.match(line)
            if not match:
                raise SubripReadError('Index not found')

            index = int(match.group('index'))
            if index != previous_index + 1:
                pass
                # FIXME: Raise or don't care? IMO: log
                # raise SubripReadError('Inconsistent index %d (previous was %d)' % (index, previous_index))
            previous_index = index

            # reset text
            text = ''

            # go to next state
            state = TIMINGS
            continue

        if state == TIMINGS:
            if '-->' not in line:
                raise SubripReadError('Timing separator not found')
            timings = line.split('-->')
            if len(timings) != 2:
                raise SubripReadError('Unexpected number of timings (%d)' % len(timings))

            # parse timings
            start_time = read_timing(timings[0].strip())
            end_time = read_timing(timings[1].strip())

            # go to next state
            state = TEXT
            continue

        if state == TEXT:
            # concatenate the cue text
            if line:
                text += line + '\n'
                continue

            # parse the full text and yield the entire cue
            yield Cue(start_time, end_time, read_text(text))

            # reset state
            state = INDEX

    else:
        # yield the last cue
        if state == TEXT:
            yield Cue(start_time, end_time, read_text(text))


def generate_lines(cues):
    for i, cue in enumerate(cues, 1):
        yield str(i)
        yield write_timing(cue.start_time) + ' --> ' + write_timing(cue.end_time)
        yield ''.join(generate_text(cue.text))
        yield ''

'''To delete
def write_child(child, template=None):
    template = template or '{children}'
    if isinstance(child, CueText):
        for k, v in child.styles.items():
            if (k, v) == ('font-weight', 'bold'):
                template = '<b>' + template + '</b>'
            elif (k, v) == ('font-style', 'italic'):
                template = '<i>' + template + '</i>'
            elif k == 'font-size':
                template = ('<font size="%d">' % v) + template + '</font>'
            elif k == 'font-color':
                template = ('<font color="%s">' % v) + template + '</font>'
            else:
                logger.warning('Unsupported style %s: %s', k, v)
    else:
        print(child)
'''


def generate_text(text):
    if isinstance(text, CueText):
        if text.styles:
            k, v = text.styles.popitem()
            if (k, v) == ('font-weight', 'bold'):
                yield '<b>'
                yield from generate_text(text)
                yield '</b>'
            elif (k, v) == ('font-style', 'italic'):
                yield '<i>'
                yield from generate_text(text)
                yield '</i>'
            elif k == 'font-size':
                yield '<font size="%d">' % v
                yield from generate_text(text)
                yield '</font>'
            elif k == 'font-color':
                yield '<font color="%s">' % v
                yield from generate_text(text)
                yield '</font>'
            else:
                logger.warning('Unsupported style %s: %s', k, v)
                yield from generate_text(text)
        else:
            for child in text.children:
                yield from generate_text(child)
    else:
        yield text


class SubripSubtitle(object):
    def __init__(self, cues):
        self.cues = []

    @classmethod
    def fromstream(cls, stream):
        return cls(list(read_cue(stream)))


if __name__ == '__main__':
    path = '/home/antoine/PycharmProjects/subliminal/tests/data/subtitles/subrip.srt'
    with open(path) as f:
        for line in generate_lines(read_cue(f)):
            print(line)
