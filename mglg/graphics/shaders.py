try:
    import importlib.resources as res
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as res
import moderngl as mgl
from . import shader_src
from .shader_src.src import *
flat_shader = None
image_shader = None
stipple_shader = None
text_shader = None
vertex_color_shader = None
particle_shader = None


def make_simple_program(context, v_file, f_file):
    vert = res.read_text(shader_src, v_file)
    frag = res.read_text(shader_src, f_file)
    return context.program(vertex_shader=vert, fragment_shader=frag)


def FlatShader(context: mgl.Context):
    global flat_shader
    if flat_shader is None:
        flat_shader = context.program(vertex_shader=flat_vert, fragment_shader=flat_frag)
    return flat_shader


def ImageShader(context: mgl.Context):
    global image_shader
    if image_shader is None:
        image_shader = context.program(vertex_shader=image_vert, fragment_shader=image_frag)
    return image_shader


def StippleShader(context: mgl.Context):
    global stipple_shader
    if stipple_shader is None:
        stipple_shader = context.program(vertex_shader=stipple_vert, fragment_shader=stipple_frag)
    return stipple_shader


def TextShader(context: mgl.Context):
    global text_shader
    if text_shader is None:
        text_shader = context.program(vertex_shader=text_vert, fragment_shader=text_frag)
    return text_shader


def VertexColorShader(context: mgl.Context):
    global vertex_color_shader
    if vertex_color_shader is None:
        vertex_color_shader = context.program(vertex_shader=vertex_color_vert, fragment_shader=vertex_color_frag)
    return vertex_color_shader
