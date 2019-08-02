from math import cos, sin
from numpy import pi, float32, eye
from mglg.graphics.cartesian import Cartesian2D, Cartesian3D


class Object2D(object):
    def __init__(self, position=(0, 0), rotation=0, scale=(1, 1), *args, **kwargs):
        #super().__init__(*args, **kwargs)
        self.position = Cartesian2D(*position)
        self.rotation = 0
        self.scale = Cartesian2D(*scale)
        self._model_matrix = eye(4, dtype=float32)

    @property
    def model_matrix(self):
        # TODO: any caching?
        mm = self._model_matrix
        make_2d_mm(self.position._array, self.rotation, self.scale._array, mm)
        return mm


def make_2d_mm(pos, rot, scal, out):
    # this beats np.radians, and imul seems slower than *
    rot = rot * (pi/180.0)
    # this beats np.cos(..., dtype=np.float32)
    s = float32(sin(rot))
    c = float32(cos(rot))
    out[0, 0] = scal[0] * c
    out[0, 1] = s * scal[0]
    out[1, 0] = -s * scal[1]  # pylint: disable=invalid-unary-operand-type
    out[1, 1] = scal[1] * c
    out[2, 2] = 1.0
    out[3, 0] = pos[0]
    out[3, 1] = pos[1]
    out[3, 3] = 1.0


if __name__ == '__main__':
    from mglg.util import timethat
    import numpy as np

    out = np.eye(4, dtype=np.float32)

    pos = (0, 0)
    rot = 34.0
    scal = (1, 1)

    # first, look at perf with
    setup = 'from __main__ import make_2d_mm, pos, rot, scal, out'
    timethat('make_2d_mm(pos, rot, scal, out)', setup=setup)

    # next, non-matching types
    pos = np.array(pos)
    scal = np.array(scal)
    timethat('make_2d_mm(pos, rot, scal, out)', setup=setup)

    # match types
    pos = pos.astype(np.float32)
    scal = scal.astype(np.float32)
    timethat('make_2d_mm(pos, rot, scal, out)', setup=setup)

    obj = Object2D()
    setup2 = 'from __main__ import obj'
    timethat('obj.model_matrix', setup=setup2)
