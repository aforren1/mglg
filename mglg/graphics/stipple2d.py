import numpy as np

import moderngl as mgl
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.shape2d import _make_2d_indexed
from mglg.graphics.shape2d import square_vertices, line_vertices, arrow_vertices, circle_vertices
from mglg.math.vector import Vec4
from mglg.graphics.shaders import StippleShader


class Stipple2D(Drawable2D):
    def __init__(self, window, vertices=None,
                 pattern=0xff00, color=(1, 1, 1, 1),
                 *args, **kwargs):
        super().__init__(window, *args, **kwargs)

        context = window.ctx
        width, height = window.size
        self.shader = StippleShader(context)
        if not hasattr(self, '_vertices'):
            self._vertices = np.array(vertices)

        vbo = context.buffer(self._vertices)
        self.vao = context.simple_vertex_array(self.shader, vbo, 'vertices')
        self._color = Vec4(color)
        self.pattern = pattern
        self.shader['u_resolution'].value = width, height
        self.shader['u_factor'].value = 2.0
        self.shader['u_pattern'].value = pattern
        self.mvp_unif = self.shader['mvp']
        self.color_unif = self.shader['color']

    def draw(self):
        if self.visible:
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.color_unif.write(self._color)
            self.vao.render(mgl.LINE_LOOP)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color.rgba = color


class StippleSquare(Stipple2D):
    _vertices = np.array(square_vertices, dtype='f4')


class StippleLine(Stipple2D):
    _vertices = np.array(line_vertices, dtype='f4')


class StippleArrow(Stipple2D):
    _vertices = np.array(arrow_vertices, dtype='f4')


class StippleCircle(Stipple2D):
    _vertices = np.array(circle_vertices, dtype='f4')
