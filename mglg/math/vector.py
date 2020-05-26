from glm import vec2, vec3, vec4

# wrapping these allows us to set on swizzles
# (not supported by glm, see e.g. https://github.com/g-truc/glm/issues/786)

lookup = {'x': 0, 'y': 1, 'z': 2, 'w': 3,
          'r': 0, 'g': 1, 'b': 2, 'a': 3}
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
            self[lookup[k]] = v


class Vec2(Vec, vec2):
    pass

class Vec3(Vec, vec3):
    pass

class Vec4(Vec, vec4):
    pass


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
