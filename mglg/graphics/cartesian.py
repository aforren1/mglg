from mglg.graphics.swizzle import Swizzle


class Cartesian3D(Swizzle):
    vals = {'x': 0, 'y': 1, 'z': 2}


class Cartesian2D(Swizzle):
    vals = {'x': 0, 'y': 1}
