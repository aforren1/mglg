try:
    import importlib.resources as res
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as res
import moderngl as mgl
from . import shader_src

# TODO: do we need to do a singleton sort of thing? What happens if
# the same shader is made in several different places?


def make_simple_program(context, v_file, f_file):
    vert = res.read_text(shader_src, v_file)
    frag = res.read_text(shader_src, f_file)
    return context.program(vertex_shader=vert, fragment_shader=frag)


def FlatShader(context: mgl.Context):
    return make_simple_program(context, 'flat.vert', 'flat.frag')


def ImageShader(context: mgl.Context):
    return make_simple_program(context, 'image.vert', 'image.frag')


def StippleShader(context: mgl.Context):
    return make_simple_program(context, 'stipple.vert', 'stipple.frag')


def TextShader(context: mgl.Context):
    return make_simple_program(context, 'text.vert', 'text.frag')


class ParticleShader(object):
    def __init__(self, context: mgl.Context):
        self.render = make_simple_program(context, 'particle.vert', 'particle.frag')
        trans_prog = res.read_text(shader_src, 'particle_transform.vert')
        self.transform = context.program(vertex_shader=trans_prog,
                                         varyings=['out_pos_alpha',
                                                   'out_prev_pos_alpha'])
