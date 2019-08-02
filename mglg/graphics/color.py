from .swizzle import Swizzle


class Color(Swizzle):
    vals = {'r': 0, 'g': 1, 'b': 2, 'a': 3}

    def __init__(self, r, g, b, a, **kwargs):
        super().__init__(r, g, b, a, **kwargs)
