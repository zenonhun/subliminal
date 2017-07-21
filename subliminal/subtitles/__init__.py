# -*- coding: utf-8 -*-
class Subtitle(object):
    def __init__(self, styles):
        self.styles = styles


class Cue(object):
    """A single subtitle cue with timings and components.

    :param datetime.timedelta start_time: start time.
    :param datetime.timedelta end_time: end time.
    :param list components: cue components.

    """
    def __init__(self, start_time, end_time, text):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

    def __repr__(self):
        return '<Cue [{start_time} -> {end_time}] {text}>'.format(start_time=self.start_time, end_time=self.end_time,
                                                                  text=repr(self.text))


class CueText(object):
    """Text with styles in a Cue."""
    def __init__(self, contents=None, styles=None):
        self.contents = contents or []
        self.styles = styles or {}

    def __iter__(self):
        return iter(self.contents)

    def __len__(self):
        return len(self.contents)

    def __getitem__(self, item):
        return self.contents[item]

    def __str__(self):
        return ''.join(str(c) for c in self)

    def __repr__(self):
        if not self.styles:
            return '<CueText>{children}</CueText>'.format(children=''.join(repr(c) for c in self))

        return '<CueText styles={styles}>{children}</CueText>'.format(styles=self.styles,
                                                                      children=''.join(repr(c) for c in self))

'''
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
'''
