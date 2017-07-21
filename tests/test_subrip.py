# -*- coding: utf-8 -*-
from datetime import timedelta

import pytest
from bs4 import Tag, NavigableString

from subliminal.subtitles import CueText
from subliminal.subtitles.subrip import read_timing, SubripReadError, write_timing, SubripWriteError, parse_texts


def test_read_timing():
    assert read_timing('12:34:56,789') == timedelta(hours=12, minutes=34, seconds=56, milliseconds=789)


def test_read_timing_no_leading_zeros():
    assert read_timing('1:2:3,456') == timedelta(hours=1, minutes=2, seconds=3, milliseconds=456)


def test_read_timing_bad_separator():
    with pytest.raises(SubripReadError):
        read_timing('12,34,56,789')


def test_read_timing_dot_for_milliseconds():
    with pytest.raises(SubripReadError):
        read_timing('12:34:56.789')


def test_write_timing():
    assert write_timing(timedelta(hours=12, minutes=34, seconds=56, milliseconds=789)) == '12:34:56,789'


def test_write_timing_leading_zeros():
    assert write_timing(timedelta(hours=1, minutes=2, seconds=3, milliseconds=456)) == '01:02:03,456'


def test_write_timing_out_of_range():
    with pytest.raises(SubripWriteError):
        write_timing(timedelta(hours=100, minutes=2, seconds=3, milliseconds=456))


def test_parse_texts():
    # create "<b><i>Hello</i> world</b>"
    parent = Tag(name='b')
    child = Tag(name='i')
    child.append('Hello')
    parent.append(child)
    parent.append(' world')

    # parse multiple elements
    texts = parse_texts([parent, NavigableString('!')])

    assert len(texts) == 2
    assert isinstance(texts[0], CueText)
    assert texts[0].styles == {'font-weight': 'bold'}
    assert len(texts[0]) == 2
    assert texts[0][0]
    assert isinstance(texts[1], str)
    assert texts[1] == '!'
