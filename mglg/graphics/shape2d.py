import numpy as np

import moderngl as mgl
from mglg.ext import earcut, flatten
from mglg.graphics.drawable import Drawable2D
from mglg.math.vector import Vec4
from mglg.graphics.shaders import FlatShader


def _make_2d_indexed(outline):
    outline = np.array(outline, dtype=np.float32)
    tmp = flatten(outline.reshape(1, -1, 2))
    indices = np.array(earcut(tmp['vertices'], tmp['holes'], tmp['dimensions']), dtype=np.uint32)
    vertices = np.zeros(outline.shape[0], dtype=[('vertices', np.float32, 3)])
    vertices['vertices'][:, :2] = outline
    return vertices.view(np.ubyte), indices.view(np.ubyte)


white = (1, 1, 1, 1)

# 2d shapes using indexed triangles


class Shape2D(Drawable2D):
    _vertices = None
    _indices = None
    _static = False  # user can subclass with `_static = True` to re-use VAO for all class instances

    def __init__(self, window,
                 vertices=None,
                 is_filled=True, is_outlined=True,
                 fill_color=white, outline_color=white,
                 *args, **kwargs):
        # context & shader go to Drawable,
        # kwargs should be position/ori/scale
        super().__init__(window, *args, **kwargs)
        shader = FlatShader(window.ctx)
        self.shader = shader

        if not hasattr(self, 'vao_fill'):
            if self._vertices is None:
                vertices, indices = _make_2d_indexed(vertices)
            else:
                vertices, indices = self._vertices, self._indices

            context = window.ctx
            vbo = context.buffer(vertices)
            ibo = context.buffer(indices)

            if not self._static:
                # TODO: any way to drop the indexing for the outline? seems silly
                # to have two
                self.vao_fill = context.simple_vertex_array(shader, vbo, 'vertices',
                                                            index_buffer=ibo)
                self.vao_outline = context.simple_vertex_array(shader, vbo, 'vertices')
            else:
                self.store_vaos(context, shader, vbo, ibo)

        self.is_filled = is_filled
        self.is_outlined = is_outlined
        self._fill_color = Vec4(fill_color)
        self._outline_color = Vec4(outline_color)
        self.mvp_unif = self.shader['mvp']
        self.color_unif = self.shader['color']

    def draw(self):
        if self.visible:
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            if self.is_filled:
                self.color_unif.write(self._fill_color)
                self.vao_fill.render(mgl.TRIANGLES)
            if self.is_outlined:
                self.color_unif.write(self._outline_color)
                self.vao_outline.render(mgl.LINE_LOOP)

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color):
        self._fill_color.rgba = color

    @property
    def outline_color(self):
        return self._outline_color

    @outline_color.setter
    def outline_color(self, color):
        self._outline_color.rgba = color

    @classmethod
    def store_vaos(cls, context, shader, vbo, ibo):
        # for common shapes, re-use the same VAO
        cls.vao_fill = context.simple_vertex_array(shader, vbo, 'vertices', index_buffer=ibo)
        cls.vao_outline = context.simple_vertex_array(shader, vbo, 'vertices')


square_vertices = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * 0.5
cross_vertices = np.array([[-1, 0.2], [-0.2, 0.2], [-0.2, 1], [0.2, 1],
                           [0.2, 0.2], [1, 0.2], [1, -0.2], [0.2, -0.2],
                           [0.2, -1], [-0.2, -1], [-0.2, -0.2], [-1, -0.2],
                           [-1, 0.2]]) * 0.5

arrow_vertices = np.array([[-1, 0.4], [0, 0.4], [0, 0.8], [1, 0],
                           [0, -0.8], [0, -0.4], [-1, -0.4]]) * 0.5
line_vertices = np.array([[-0.5, 0], [0.5, 0]])


class Square(Shape2D):
    _static = True
    _vertices, _indices = _make_2d_indexed(square_vertices)


class Cross(Shape2D):
    _static = True
    _vertices, _indices = _make_2d_indexed(cross_vertices)


class Arrow(Shape2D):
    _static = True
    _vertices, _indices = _make_2d_indexed(arrow_vertices)


def make_poly_outline(segments=64):
    vertices = []
    angle_increment = 2 * np.pi / segments
    for i in range(segments + 1):
        angle = i * angle_increment
        vertices.append((np.cos(angle), np.sin(angle)))
    return np.array(vertices) * 0.5


class Polygon(Shape2D):
    def __init__(self, window, segments=32, *args, **kwargs):
        vertices = make_poly_outline(segments)
        super().__init__(window, vertices=vertices, *args, **kwargs)


circle_vertices = make_poly_outline(256)


class Circle(Shape2D):
    _static = True
    _vertices, _indices = _make_2d_indexed(circle_vertices)


if __name__ == '__main__':
    from mglg.graphics.drawable import DrawableGroup
    from mglg.graphics.shaders import FlatShader
    from mglg.graphics.win import Win
    import glm

    win = Win()

    sqr = Square(win, scale=(0.15, 0.1), fill_color=(0.7, 0.9, 0.2, 1))
    circle = Circle(win, scale=(0.15, 0.1), fill_color=(0.2, 0.9, 0.7, 1))
    arrow = Arrow(win, scale=(0.15, 0.1), fill_color=(0.9, 0.7, 0.2, 1))
    circle.position.x += 0.2
    arrow.position.x -= 0.2
    sqr2 = Square(win, scale=(0.05, 0.05), fill_color=(0.1, 0.1, 0.1, 0.6))
    poly = Polygon(win, segments=7, scale=(0.08, 0.08), position=(-0.2, -0.2),
                   fill_color=(0.9, 0.2, 0.2, 0.5), outline_color=(0.1, 0.1, 0.1, 1))
    crs = Cross(win, fill_color=(0.2, 0.1, 0.9, 0.7), is_outlined=False,
                scale=(0.12, 0.10), position=(0.3, 0.3))

    # check that they *do* share the same vertex buffer
    assert sqr.vao_fill == sqr2.vao_fill

    dg = DrawableGroup([sqr, sqr2, circle, arrow, poly, crs])

    counter = 0
    for i in range(300):
        counter += 3
        sqr2.position.x = np.sin(counter/200)/2
        #sqr2.position.y = sqr2.position.x
        sqr2.rotation = counter
        sqr.rotation = -counter
        arrow.rotation = counter
        circle.rotation = counter
        dg.draw()
        win.flip()
        if win.should_close:
            break

        # if win.dt > 0.02:
        #     print(win.dt)
