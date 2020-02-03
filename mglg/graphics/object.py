from math import cos, sin
from numpy import pi, float32, eye
from mglg.math.vector import Vec2
from glm import mat4, vec3, radians, translate, rotate, scale


class Object2D(object):
    def __init__(self, position=(0, 0), rotation=0, scale=(1, 1), *args, **kwargs):
        self._position = Vec2(position)
        self._rotation = rotation
        self._scale = Vec2(scale)

    @property
    def model_matrix(self):
        out = mat4()
        out = translate(out, vec3(self._position, 0.0))
        out = rotate(out, radians(self._rotation), vec3(0.0, 0.0, 1.0))
        out = scale(out, vec3(self._scale, 1.0))
        return out

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position.xy = value

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale.xy = value


if __name__ == '__main__':
    from mglg.util import timethat
    import numpy as np

    obj = Object2D()
    setup2 = 'from __main__ import obj'
    timethat('obj.model_matrix', setup=setup2)
