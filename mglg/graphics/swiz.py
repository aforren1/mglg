import numpy as np

# TODO: rather than slices, could do logical indexing
# just a little bit slower (~200-300ns?), and then
# we could write something to auto-generate all swizzle
# combinations? But that doesn't help if we need to
# get a reversed version, e.g. Vec4f.yx

# but it looks like indexing with a numpy array (e.g. np.array([0, 1, 2]))
# is ever faster than slicing? So then we *can* pregenerate all
# combinations xxxx, xxxy, xxxz, xxxw, yxxxx, yxxy,
# and have pretty good perf


def generate_swiz(input_str):
    lst = list(input_str)
    ln = len(lst)

    grid = np.array(np.meshgrid(*([lst] * ln))).T.reshape(-1, ln)
    idxing = np.empty_like(grid, dtype=np.int)
    grid2 = [''.join(q) for q in grid]

    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            idxing[i, j] = input_str.find(grid[i, j])

    out_dct = {}
    for i, j in zip(grid2, idxing):
        out_dct[i] = j
    return out_dct


class Value(object):
    def __init__(self, slc=None):
        self.slc = slc

    def __get__(self, instance, owner):
        return instance._array[self.slc]

    def __set__(self, instance, value):
        instance._array[self.slc] = value


class VectorBase(object):
    def __init__(self, initial=0):
        self._array = np.zeros(0)
        self._ubyte_view = self._array.view(np.ubyte)

    def __getitem__(self, key):
        return self._array.__getitem__(key)

    def __setitem__(self, key, value):
        self._array.__setitem__(key, value)

    def __repr__(self):
        return self._array.__repr__()


class Tmp(VectorBase):


class Vector2f(VectorBase):
    x = Value(slc=0)
    y = Value(slc=1)
    xy = Value(slc=slice(0, 2))

    r = Value(slc=0)
    g = Value(slc=1)
    rg = Value(slc=slice(0, 2))

    def __init__(self, initial=0):
        self._array = np.zeros(2, dtype=np.float32)
        self._ubyte_view = self._array.view(np.ubyte)
        self.xy = initial


class Vector3f(Vector2f):
    # NB: if possible, access contiguous sections (3x faster)
    z = Value(slc=2)
    yz = Value(slc=slice(1, 3))
    xz = Value(slc=[0, 2])
    xyz = Value(slc=slice(0, 3))

    b = Value(slc=2)
    gb = Value(slc=slice(1, 3))
    rb = Value(slc=[0, 2])
    rgb = Value(slc=slice(0, 3))

    def __init__(self, initial=0):
        self._array = np.zeros(3, dtype=np.float32)
        self._ubyte_view = self._array.view(np.ubyte)
        self.xyz = initial


class Vector4f(Vector3f):
    w = Value(slc=3)
    zw = Value(slc=slice(2, 4))
    yw = Value(slc=[1, 3])
    xw = Value(slc=[0, 3])
    yzw = Value(slc=slice(1, 4))
    xyw = Value(slc=[0, 1, 3])
    xzw = Value(slc=[0, 2, 3])
    xyzw = Value(slc=slice(0, 4))

    a = Value(slc=3)
    ba = Value(slc=slice(2, 4))
    ga = Value(slc=[1, 3])
    ra = Value(slc=[0, 3])
    gba = Value(slc=slice(1, 4))
    rga = Value(slc=[0, 1, 3])
    rba = Value(slc=[0, 2, 3])
    rgba = Value(slc=slice(0, 4))

    def __init__(self, initial=0):
        self._array = np.zeros(4, dtype=np.float32)
        self._ubyte_view = self._array.view(np.ubyte)
        self.xyzw = initial  # scalar or tuple/array
