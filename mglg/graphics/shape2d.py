import numpy as np

import moderngl as mgl
from mglg.ext import earcut, flatten
from mglg.graphics.drawable import Drawable2D
from mglg.math.vector import Vec4
from glm import vec4
from mglg.graphics.outline import generate_outline

def _make_2d_indexed(outline):
    verts, inds = generate_outline(outline, True)
    # run earcut on the inner part
    tmp = flatten(verts['vertices'][1:-2:2].reshape(1, -1, 2))
    indices = np.array(earcut(tmp['vertices'], tmp['holes'], tmp['dimensions']), dtype=np.int32)
    # add to existing indices
    indices *= 2
    indices += 1
    indices = np.hstack((indices, inds))
    return verts, indices


white = (1, 1, 1, 1)

# 2d shapes using indexed triangles
flat_frag = """
#version 330
flat in vec4 color;
out vec4 f_color;
void main()
{
    f_color = color;
}"""

flat_vert = """
#version 330
uniform mat4 mvp;
uniform vec4 fill_color;
uniform vec4 outline_color;
uniform float thickness;

in vec2 vertices;
in vec2 normal;
in float miter;
in int outer;

flat out vec4 color;

void main()
{
    vec2 point_pos = vertices + mix(vec2(0, 0), normal * thickness * miter, outer);
    color = mix(fill_color, outline_color, outer);
    gl_Position = mvp * vec4(point_pos, 0.0, 1.0);
}
"""

tmp_shader = None
def TmpShader(context):
    global tmp_shader
    if tmp_shader is None:
        tmp_shader = context.program(vertex_shader=flat_vert, fragment_shader=flat_frag)
    return tmp_shader

class Shape2D(Drawable2D):
    _vertices = None
    _indices = None
    _static = False  # user can subclass with `_static = True` to re-use VAO for all class instances

    def __init__(self, window,
                 vertices=None,
                 is_filled=True, is_outlined=True,
                 outline_thickness=0.05,
                 fill_color=white, outline_color=white,
                 *args, **kwargs):
        # context & shader go to Drawable,
        # kwargs should be position/ori/scale
        super().__init__(window, *args, **kwargs)
        shader = TmpShader(window.ctx)
        self.shader = shader
        for name in shader:
            member = shader[name]
            print(name, type(member), member)

        if not hasattr(self, 'vao'):
            if self._vertices is None:
                vertices, indices = _make_2d_indexed(vertices)
            else:
                vertices, indices = self._vertices, self._indices

            print(vertices, indices)
            ctx = window.ctx
            vbo = ctx.buffer(vertices)
            ibo = ctx.buffer(indices)

            if not self._static:
                self.vao = ctx.vertex_array(shader, [(vbo, '2f 2f 1f 1i', 'vertices', 'normal', 'miter', 'outer')],
                                            index_buffer=ibo)
            else:
                self.store_vaos(ctx, shader, vbo, ibo)

        self.is_filled = is_filled
        self.is_outlined = is_outlined
        self._fill_color = Vec4(fill_color)
        self._outline_color = Vec4(outline_color)
        self.mvp_unif = shader['mvp']
        self.fill_unif = shader['fill_color']
        self.outline_unif = shader['outline_color']
        self.thick_unif = shader['thickness']
        self.thick_unif.value = outline_thickness

    def draw(self):
        if self.visible:
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            if self.is_filled:
                self.fill_unif.write(self._fill_color)
            else:
                self.fill_unif.write(vec4(1.0, 1, 1, 0))
            if self.is_outlined:
                self.outline_unif.write(self._outline_color)
            else:
                self.outline_unif.write(self._fill_color)
            self.vao.render(mgl.TRIANGLES)

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
    def store_vaos(cls, ctx, shader, vbo, ibo):
        # for common shapes, re-use the same VAO
        cls.vao = ctx.vertex_array(shader, [(vbo, '2f 2f 1f 1i', 'vertices', 'normal', 'miter', 'outer')],
                                   index_buffer=ibo)


square_vertices = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * 0.5
cross_vertices = np.array([[-1, 0.2], [-0.2, 0.2], [-0.2, 1], [0.2, 1],
                           [0.2, 0.2], [1, 0.2], [1, -0.2], [0.2, -0.2],
                           [0.2, -1], [-0.2, -1], [-0.2, -0.2], [-1, -0.2],
                           [-1, 0.2]]) * 0.5
cross_vertices = cross_vertices[::-1]

arrow_vertices = np.array([[-1, 0.4], [0, 0.4], [0, 0.8], [1, 0],
                           [0, -0.8], [0, -0.4], [-1, -0.4]]) * 0.5
line_vertices = np.array([[-0.5, 0], [0.5, 0]])


class Square(Shape2D):
    _static = False
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
    for i in range(1, segments + 1):
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

    sqr = Square(win, scale=(0.15, 0.1), fill_color=(0.7, 0.9, 0.2, 1), is_outlined=False)
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
    # assert sqr.vao_fill == sqr2.vao_fill

    dg = DrawableGroup([sqr, sqr2, circle, arrow, poly, crs])

    counter = 0
    for i in range(3000):
        counter += 1
        sqr2.position.x = np.sin(counter/200)/2
        sqr2.position.y = sqr2.position.x
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
