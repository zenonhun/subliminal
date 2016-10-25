# -*- coding: utf-8 -*-
from datetime import time


class Subtitle(object):
    def __init__(self, styles):
        self.styles = styles


class CueText(object):
    def __init__(self, children, styles=None):
        self.styles = styles or {}
        self.children = children

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return ''.join(str(c) for c in self.children)

    def __repr__(self):
        return '<{name} styles={styles}>{children}</{name}>'.format(name=self.__class__.__name__, styles=self.styles,
                                                                    children=''.join(repr(c) for c in self.children))


class Component(object):
    """Base class for cue text.

    :param list components: sub-components of this one.

    """

    def __init__(self, components=None):
        if components is None:
            self.components = []
        elif isinstance(components, list):
            self.components = components
        else:
            self.components = [components]

    def __iter__(self):
        return iter(self.components)

    def __len__(self):
        return len(self.components)

    def __str__(self):
        return ''.join(str(c) for c in self.components)

    def __repr__(self):
        return '<{name}>{components}</{name}>'.format(name=self.__class__.__name__,
                                                      components=''.join(repr(c) for c in self.components))


class Bold(Component):
    """Bold :class:`Component`."""


class Italic(Component):
    """Italic :class:`Component`."""


class Underline(Component):
    """Underline :class:`Component`."""


class Strikethrough(Component):
    """Strikethrough :class:`Component`."""


class Font(Component):
    """Font :class:`Component`."""
    def __init__(self, color, size, *args, **kwargs):
        super(Font, self).__init__(*args, **kwargs)
        self.color = color
        self.size = size

    def __repr__(self):
        return '<{name} color="{color}" size={size}>{components}</{name}>'.format(
            name=self.__class__.__name__, color=self.color, size=self.size,
            components=''.join(repr(c) for c in self.components)
        )


class Cue(object):
    """A single subtitle cue with timings and components.

    :param datetime.time start_time: start time.
    :param datetime.time end_time: end time.
    :param list components: cue components.

    """
    def __init__(self, start_time, end_time, components):
        self.start_time = start_time
        self.end_time = end_time
        self.components = components

    def __repr__(self):
        return '<Cue [{start_time} -> {end_time}] {text}>'.format(start_time=self.start_time, end_time=self.end_time,
                                                                  text=''.join(repr(c) for c in self.components))


if __name__ == '__main__':
    cue = Cue(time(), time(1), [Bold('Hello')])
    print repr(cue)
