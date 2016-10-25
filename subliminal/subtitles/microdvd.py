# -*- coding: utf-8 -*-
from datetime import time
import logging
import re

from bs4 import NavigableString, Tag
import six

from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitles import Bold, Cue, Font, Italic, Underline

logger = logging.getLogger(__name__)

#: Line parsing regex
line_re = re.compile(r'{(?P<start_frame>\d+)}{(?P<stop_frame>\d+)}(?P<text>.*)')

#: Control parsing regex
control_re = re.compile(r'{(?P<code>[yYfFsScC]):(?P<value>[\w$]+)}')


class MicroDVDReadError(Exception):
    """Exception raised on reading error."""
    pass


def read_cue(stream):
    """Generate Cues from a text stream.

    :param stream: the text stream.
    :return: the parsed cue.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Cue`]

    """

    for line in stream:
        line = line.strip()

        line_match = line_re.match(line)

        for cue_line in line_match.group('text').split('|'):
            cue_styles = {}
            while True:
                control_match = control_re.match(cue_line)
                if not control_match:
                    break

                cue_line = cue_line[control_match.endpos]


def parse_components(elements):
    """Generate :class:`~subliminal.subtitles.Component` from an iterable of
    :class:`~bs4.Tag` or :class:`~bs4.NavigableString`.

    :param list elements: the elements to parse.
    :return: the parsed component.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Component`]

    """
    for element in elements:
        if isinstance(element, Tag):
            if element.name == 'b':
                yield Bold(list(parse_components(element.children)))
            elif element.name == 'i':
                yield Italic(list(parse_components(element.children)))
            elif element.name == 'u':
                yield Underline(list(parse_components(element.children)))
            elif element.name == 'font':
                yield Font(element.attrs.get('color'), element.attrs.get('size'),
                           list(parse_components(element.children)))
            else:
                raise ValueError('Unknown tag %r' % element.name)
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

    for path in glob.glob('tests/data/subtitles/*.sub'):
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
            print 'KO:', os.path.basename(path)
