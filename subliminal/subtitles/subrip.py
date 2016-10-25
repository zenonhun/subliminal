# -*- coding: utf-8 -*-
from datetime import time
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


def read_cue(stream):
    """Generate Cues from a text stream.

    :param stream: the text stream.
    :return: the parsed cue.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Cue`]

    """
    state = INDEX
    text = ''
    start_time = end_time = time()
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

            # parse start time
            match = timing_re.match(timings[0].strip())
            if not match:
                raise SubripReadError('Failed to parse timing %r' % timings[0])
            start_time = time(int(match.group('hour')), int(match.group('minute')), int(match.group('second')),
                              int(match.group('millisecond')) * 1000)

            # parse end time
            match = timing_re.match(timings[1].strip())
            if not match:
                raise SubripReadError('Failed to parse timing %r' % timings[1])
            end_time = time(int(match.group('hour')), int(match.group('minute')), int(match.group('second')),
                            int(match.group('millisecond')) * 1000)

            # go to next state
            state = TEXT
            continue

        if state == TEXT:
            # concatenate the cue text
            if line:
                text += line + '\n'
                continue

            # parse the full text and yield the entire cue
            soup = ParserBeautifulSoup(text.strip(), ['lxml', 'html.parser'])
            cue = Cue(start_time, end_time, list(parse_components(soup.children)))
            logger.debug('Parsed cue %r', cue)
            yield cue

            # reset state
            state = INDEX


def parse_components(elements):
    """Recursively generate :class:`~subliminal.subtitles.CueText` from an iterable of
    :class:`~bs4.Tag` or :class:`~bs4.NavigableString`.

    :param list elements: the elements to parse.
    :return: the parsed component.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Component`]

    """
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

            # yield the cue text with its children and styles
            yield CueText(parse_components(element.children), styles=styles)
        elif isinstance(element, NavigableString):
            yield six.text_type(element)
        else:
            raise ValueError('Unknown element %r' % element)


def write_cue(cue):
    pass


class SubripSubtitle(object):
    def __init__(self, cues):
        self.cues = []

    @classmethod
    def fromstream(cls, stream):
        return cls(list(read_cue(stream)))


if __name__ == '__main__':
    import io
    import os
    import glob
    import chardet

    for path in glob.glob('/media/blackhole/movies/L*/*.srt'):
        with open(path, 'rb') as f:
            encoding = chardet.detect(f.read())['encoding']
        try:
            with io.open(path, encoding=encoding) as f:
                for cue in read_cue(f):
                    pass
                print 'OK:', os.path.basename(path)
        except UnicodeDecodeError:
            print 'KO Unicode:', os.path.basename(path)
        except:
            raise
