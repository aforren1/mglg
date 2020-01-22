from glm import vec2, vec3, vec4

# wrapping these allows us to set on swizzles
# (not supported by glm, see e.g. https://github.com/g-truc/glm/issues/786)


class Vec(object):
    def __setattr__(self, keys, vals):
        try:
            vals[0]
            isiter = True
        except (TypeError, IndexError):
            isiter = False
        for i in range(len(keys)):
            k = keys[i]
            v = vals[i] if isiter else vals
            self._swizzle(k, v)

    def _swizzle(self, k, v):
        raise ValueError('Missing implementation.')


class Vec2(Vec, vec2):
    def _swizzle(self, k, v):
        if k in 'xr':
            self[0] = v
        elif k in 'yg':
            self[1] = v


class Vec3(Vec, vec3):
    def _swizzle(self, k, v):
        if k in 'xr':
            self[0] = v
        elif k in 'yg':
            self[1] = v
        elif k in 'zb':
            self[2] = v


class Vec4(Vec, vec4):
    def _swizzle(self, k, v):
        if k in 'xr':
            self[0] = v
        elif k in 'yg':
            self[1] = v
        elif k in 'zb':
            self[2] = v
        elif k in 'wa':
            self[3] = v


if __name__ == '__main__':
    import timeit
    import numpy as np
    from mglg.util import timethat

    x = np.array([1, 2, 3, 4], dtype=np.float32)
    y = Vec4([1, 2, 3, 4])

    timethat('x[0]', globs=globals())
    timethat('x[:]', globs=globals())
    timethat('x[[0, 3, 1]]', globs=globals())

    timethat('y[0]', number=1e7, globs=globals())
    timethat('y.x', number=1e7, globs=globals())
    timethat('y.xyzw', number=1e7, globs=globals())
    timethat('y.xwy', number=1e7, globs=globals())
