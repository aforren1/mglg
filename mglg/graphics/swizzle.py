from itertools import product
from operator import setitem
import numpy as np

# this is adapted from github.com/ratcave/ratcave
# TODO: switch to numpy structured arrays/recarrays?
# faster access?, but looks like it doesn't let us
# do arithmetic on multiple fields
# dtype = [('x', np.float32), ('y', np.float32), ('z', np.float32)]
# or what about named tuples? can still be backed by numpy array
# except can't modify named tuples, how about dataclasses?


class Swizzle(object):

    vals = {}

    def __init__(self, *args, **kwargs):
        " Returns a Swizzle object"
        self._array = np.array(args, dtype=np.float32)
        # to the benefit of moderngl, so we can use `write()` instead of `value`
        self._ubyte_view = self._array.view(np.ubyte)
        self._init_val_properties()

    def _init_val_properties(self):
        """
        Generates combinations of named coordinate values, mapping them to the internal array.
        For Example: x, xy, xyz, y, yy, zyx, etc
        """
        def gen_getter_setter_funs(*args):
            indices = [self.vals[val] for val in args]

            def getter(self):
                return tuple(self._array[indices]) if len(args) > 1 else self._array[indices[0]]

            def setter(self, value):
                setitem(self._array, indices, value)

            return getter, setter

        for n_repeats in range(1, len(self.vals)+1):
            for args in product(self.vals.keys(), repeat=n_repeats):
                getter, setter = gen_getter_setter_funs(*args)
                setattr(self.__class__, ''.join(args), property(fget=getter, fset=setter))

    def __getitem__(self, item):
        if type(item) == slice:
            return tuple(self._array[item])
        return self._array[item]

    def __setitem__(self, idx, value):
        self._array[idx] = value

    def __repr__(self):
        arg_str = ', '.join(['{}={}'.format(*el) for el in zip(''.join(self.vals.keys()), self._array)])
        return "{cls}({coords})".format(cls=self.__class__.__name__, coords=arg_str)
