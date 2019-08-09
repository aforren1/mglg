import numpy as np
from itertools import product


def generate_swiz(input_str):
    ln = len(input_str) + 1
    out = {}
    # for each
    for num in range(1, ln):
        # generate all permutations (which will be the keys we use to access the array)
        perms = list(product(input_str, repeat=num))
        perms = [''.join(z) for z in perms]
        # generate index of that
        indices = []
        for p in perms:
            idx = []
            for inp in p:
                idx.append(input_str.find(inp))
            # Detect if we can use a slice instead
            dff = np.diff(idx)
            if dff.shape[0] != 0 and (abs(dff) == 1).all() and np.unique(dff).size == 1:
                sgn = np.sign(dff[0])
                # if positive, pos slice
                # otherwise, negative slice
                imin = min(idx)
                imax = max(idx)
                if sgn > 0:
                    indices.append(slice(imin, imax+1, 1))
                else:
                    if imin == 0:
                        imin = None
                    indices.append(slice(imax, imin, -1))
            else:
                indices.append(np.array(idx, dtype=np.intp))
        for i, j in zip(perms, indices):
            out.update({i: j})
    return out


class Value(object):
    def __init__(self, slc=None):
        self.slc = slc

    def __get__(self, instance, owner):
        return instance._array[self.slc]

    def __set__(self, instance, value):
        instance._array[self.slc] = value


class VectorBase(object):

    _xyzw = 'xyzw'
    _rgba = 'rgba'

    def __init_subclass__(cls, length, dtype, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._length = length
        cls._dtype = dtype
        swiz = generate_swiz(cls._xyzw[:length])
        swiz.update(generate_swiz(cls._rgba[:length]))

        for key in swiz.keys():
            setattr(cls, key, Value(swiz[key]))

    def __init__(self, initial=0):
        self._array = np.zeros(self._length, dtype=self._dtype)
        self._array[:] = initial
        self._ubyte_view = self._array.view(np.ubyte)

    def __getitem__(self, key):
        return self._array.__getitem__(key)

    def __setitem__(self, key, value):
        self._array.__setitem__(key, value)

    def __repr__(self):
        return self._array.__repr__()


class Vector2f(VectorBase, length=2, dtype=np.float32):
    pass


class Vector3f(VectorBase, length=3, dtype=np.float32):
    pass


class Vector4f(VectorBase, length=4, dtype=np.float32):
    pass


if __name__ == '__main__':
    import timeit

    def timethat(expr, number=int(1e6), setup='pass', globs=globals()):
        title = expr
        print('{:60} {:8.5f} µs'.format(title, timeit.timeit(expr, number=number, globals=globs, setup=setup)*1000000.0/number))

    x = np.array([1, 2, 3, 4], dtype=np.float32)
    y = Vector4f([1, 2, 3, 4])

    slc = slice(0, 3)
    dmb = [0, 1, 2]
    smt = np.array(dmb, dtype=np.intp)
    sm2 = np.array([1], dtype=np.intp)

    timethat('x[slc]')
    timethat('x[dmb]')
    timethat('x[smt]')
    timethat('x[sm2]')
    timethat('x[0]')

    timethat('y[slc]')
    timethat('y._array[slc]')
    timethat('y[dmb]')
    timethat('y[smt]')
    timethat('y[0]')

    timethat('y.x')
    timethat('y.xyzw')
    timethat('y.xwy')
