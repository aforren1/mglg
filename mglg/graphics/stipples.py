import numpy as np

import moderngl as mgl
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.shapes import _make_2d_indexed
from mglg.graphics.shapes import rect_vertices, line_vertices, arrow_vertices, circle_vertices
from mglg.math.vector import Vec4

# Stipple shader is from https://stackoverflow.com/a/55088683/2690232
stipple_vert = """

#version 330

layout (location = 0) in vec2 vertices;

flat out vec2 start_pos;
out vec2 vert_pos;

uniform mat4 mvp;

void main()
{
    vec4 pos    = mvp * vec4(vertices, 0.0, 1.0);
    gl_Position = pos;
    vert_pos     = pos.xy / pos.w;
    start_pos    = vert_pos;
}

"""

stipple_frag = """
#version 330

flat in vec2 start_pos;
in vec2 vert_pos;

out vec4 f_color;

uniform vec2  u_resolution;
uniform uint  u_pattern;
uniform float u_factor;
uniform vec4 color;

void main()
{
    vec2  dir  = (vert_pos-start_pos) * u_resolution/2.0;
    float dist = length(dir);

    uint bit = uint(round(dist / u_factor)) & 15U;
    if ((u_pattern & (1U<<bit)) == 0U)
        discard;
    f_color = color;
}
"""

stipple_shader = None
def StippleShader(context: mgl.Context):
    global stipple_shader
    if stipple_shader is None:
        stipple_shader = context.program(vertex_shader=stipple_vert,
                                         fragment_shader=stipple_frag)
    return stipple_shader


class StippleShape(Drawable2D):
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

    def draw(self, vp=None):
        if self.visible:
            vp = vp if vp else self.win.vp
            mvp = vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.color_unif.write(self._color)
            self.vao.render(mgl.LINE_LOOP)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color.rgba = color


class StippleRect(StippleShape):
    _vertices = np.array(rect_vertices, dtype='f4')


class StippleLine(StippleShape):
    _vertices = np.array(line_vertices, dtype='f4')


class StippleArrow(StippleShape):
    _vertices = np.array(arrow_vertices, dtype='f4')


class StippleCircle(StippleShape):
    _vertices = np.array(circle_vertices, dtype='f4')
