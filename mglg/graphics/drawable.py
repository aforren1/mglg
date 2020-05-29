import abc
import numpy as np
from mglg.graphics.object import Object2D

class Drawable(abc.ABC):
    def __init__(self, window, visible=True, *args, **kwargs):
        # window should have moderngl context, width/height, and view*projection matrix
        super().__init__(*args, **kwargs)
        self.win = window
        self.visible = visible

    @abc.abstractmethod
    def draw(self, vp=None):
        pass
        # if self.visible:
        #     ....

class Drawable2D(Drawable, Object2D):
    pass

class DrawableGroup(list):
    # at this point, it's just a dumb list of things using the
    # same shader-- for glumpy, it made a little more sense 'cause
    # the program was explicitly bound/unbound
    # moderngl maintains which program was bound last, so this does
    # provide the same effective benefit -- not calling a bunch of `glUseProgram`s

    # the other benefit is toggling visibility for a large number of Drawables
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible = True

    def draw(self, vp=None):
        if self.visible:
            for obj in self:
                obj.draw(vp)
