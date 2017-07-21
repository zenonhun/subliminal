# -*- coding: utf-8 -*-
from __future__ import division
from datetime import datetime, time, timedelta
import logging
import re

from bs4 import NavigableString, Tag
import six

from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitles import Bold, Cue, Font, Italic, Underline, CueText

logger = logging.getLogger(__name__)

#: Cue parsing regex
cue_re = re.compile(r'^{(?P<start_frame>\d+)}{(?P<stop_frame>\d+)}(?P<styles>(?:{[YFSC]:[\w,$]+})*)(?P<lines>.*)$')

# Line parsing regex
line_re = re.compile(r'^(?P<styles>(?:{[yfsc]:[\w,$]+})*)(?P<text>.*)$')

#: Control parsing regex
control_re = re.compile(r'{(?P<code>[yYfFsScC]):(?P<value>[\w,$]+)}')


class MicroDVDReadError(Exception):
    """Exception raised on reading error."""
    pass


def read_cue(stream, fps=25):
    """Generate Cues from a text stream.
    
    {2586}{2679}Something is coming.|Something hungry for blood.

    {start_frame}{stop_frame}{Y:b,i}{c:$0000ff}{s:10}Don't|{y:u}Panic!
    `-----------------------´`-----´`--------------------------------´
             timings        cue styles            lines
                                     `-------------´`----´
                       first line ->     styles      text
                                                          `----´`-----´
                                          second line ->  styles  text
    
    line ending character separate cues.

    :param stream: the text stream.
    :param int fps: frame per second of the video.
    :return: the parsed cue.
    :rtype: collections.Iterable[:class:`~subliminal.subtitles.Cue`]

    """

    for line in stream:
        line = line.strip()
        match = cue_re.match(line)

        if not match:
            raise ValueError('Cue does not match')

        # read timings
        start_time = (datetime.min + timedelta(seconds=int(match.group('start_frame')) / fps)).time()
        end_time = (datetime.min + timedelta(seconds=int(match.group('stop_frame')) / fps)).time()

        # read components
        if match.group('styles'):
            components = [CueText(list(parse_components(match.group('lines').split('|'))),
                                  styles=parse_styles(match.group('styles')))]
        else:
            components = list(parse_components(match.group('lines').split('|')))

        yield Cue(start_time, end_time, components)


def parse_components(lines):
    last = len(lines) - 1
    for i, line in enumerate(lines):
        match = line_re.match(line)

        if not match:
            raise ValueError('Line does not match')

        if match.group('styles'):
            yield CueText([match.group('text')], styles=parse_styles(match.group('styles')))
        else:
            yield match.group('text')
        if i != last:
            yield '\n'


def parse_styles(controls):
    styles = {}

    while controls:
        # match the control
        match = control_re.match(controls)
        if not match:
            raise ValueError('Control does not match')
        code, value = match.group('code').upper(), match.group('value')

        # parse the value for each possible code
        if code == 'Y':
            for value in value.split(','):
                if value == 'b':
                    styles['font-weight'] = 'bold'
                elif value == 'i':
                    styles['font-style'] = 'italic'
                elif value == 'u':
                    styles['text-decoration'] = 'underline'
                elif value == 's':
                    styles['text-decoration'] = 'line-through'
                else:
                    raise ValueError('Unsupported control value for code')
        elif code == 'F':
            styles['font-family'] = value
        elif code == 'S':
            styles['font-size'] = int(value)
        elif code == 'C':
            styles['font-color'] = '#' + value[5:7] + value[3:5] + value[1:3]
        else:
            raise ValueError('Unsupported control code')

        controls = controls[match.regs[0][1]:]

    return styles


def write_cue(cue):
    pass


class SubripSubtitle(object):
    def __init__(self, cues):
        self.cues = []

    @classmethod
    def fromstream(cls, stream):
        return cls(list(read_cue(stream)))


if __name__ == '__main__':
    print(list(parse_styles('{S:10}{Y:s}{y:i,b}')))
    print(list(parse_components(['{y:i,b}Hello', '{s:16}World!'])))
    with open('tests/data/subtitles/microdvd.sub') as f:
        for cue in read_cue(f):
            print(cue)