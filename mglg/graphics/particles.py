import numpy as np
import moderngl as mgl
from timeit import default_timer
from mglg.graphics.drawable import Drawable2D
from mglg.graphics._particle import ParticleEmitter

pvert = """
#version 330
uniform mat4 vp; // depends on screen dims
uniform vec2 g_pos; // "global" position of particle cloud
uniform vec2 g_scale; // global scale

// shared by all instances
in vec2 vertices;
in vec2 texcoord;
out vec2 v_texcoord;

// per particle
in vec2 pos;
in float scale;
in vec4 color;
out vec4 p_color;
void main()
{
    vec2 tmp = ((vertices) * scale + pos) * g_scale * 0.5 + g_pos;
    gl_Position = vp * vec4(tmp, 0.0, 1.0);
    v_texcoord = texcoord;
    p_color = color;
}
"""

pfrag = """
#version 330
uniform sampler2D texture;
in vec4 p_color; // per particle color
in vec2 v_texcoord;
out vec4 f_color;
void main()
{
    f_color = texture2D(texture, v_texcoord) * p_color;
}
"""

# from https://stackoverflow.com/a/56923189/2690232
# define normalized 2D gaussian
def gaus2d(x=0, y=0, mx=0, my=0, sx=1, sy=1):
    return 1. / (2. * np.pi * sx * sy) * np.exp(-((x - mx)**2. / (2. * sx**2.) + (y - my)**2. / (2. * sy**2.)))

def make_particle_texture():
    x = np.linspace(-5, 5, 64)
    y = np.linspace(-5, 5, 64)
    x, y = np.meshgrid(x, y) # get 2D variables instead of 1D
    z = gaus2d(x, y)
    z /= np.max(z)
    out = np.full((64, 64, 4), 1, dtype='f4')
    out[:, :, 3] = z # only alpha channel should be fading
    return out

texture_cache = {}

particle_shader = None
def ParticleShader(context: mgl.Context):
    global particle_shader
    if particle_shader is None:
        particle_shader = context.program(vertex_shader=pvert, 
                                       fragment_shader=pfrag)
    return particle_shader


class Particles(Drawable2D):
    def __init__(self, win, num_particles=1e4, *args, **kwargs):
        super().__init__(win, *args, **kwargs)
        ctx = win.ctx
        self.prog = ParticleShader(ctx)
        self._emitter = ParticleEmitter(max_particles=num_particles, *args, **kwargs)
        self.visible = False
        self.particle_vbo = ctx.buffer(dynamic=True, reserve=int(28*num_particles))
        # shared data
        vt = np.empty(4, dtype=[('vertices', '2f4'), ('texcoord', '2f4')])
        vt['vertices'] = [(-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]
        vt['texcoord'] = [(0, 1), (0, 0), (1, 1), (1, 0)]
        vbo = ctx.buffer(vt.view(np.ubyte))
        self.vao = ctx.vertex_array(
            self.prog,
            [(vbo, '2f 2f', 'vertices', 'texcoord'),
             (self.particle_vbo, '2f 1f 4f/i', 'pos', 'scale', 'color')]
        )
        particle = make_particle_texture()
        imbytes = particle.tobytes()
        imhash = hash(imbytes)
        if imhash in texture_cache.keys():
            self.texture = texture_cache[imhash]
        else:
            self.texture = ctx.texture(particle.shape[:2], 4, imbytes, dtype='f4')
            texture_cache[imhash] = self.texture
        # access uniforms
        self.u_vp = self.prog['vp']
        self.u_g_pos = self.prog['g_pos']
        self.u_g_scale = self.prog['g_scale']
        self.dt = win.dt

    def spawn(self, num_particles):
        self._emitter.spawn(num_particles)
        self.visible = True
    
    def draw(self, vp=None):
        if self.visible:
            gpuview = self._emitter.update(self.dt)
            # ideally I'd return the particle count too,
            # but it wasn't allowed by cython? So stored as
            # member of the emitter
            count = self._emitter.count
            if count > 0:
                # we have at least one particle
                win = self.win
                self.texture.use()
                vp = vp if vp else win.vp
                self.u_vp.write(vp)
                self.u_g_pos.write(self.position)
                self.u_g_scale.write(self.scale)
                self.particle_vbo.write(gpuview)
                win.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE
                self.vao.render(mgl.TRIANGLE_STRIP, instances=count)
                #self.particle_vbo.orphan()                
                win.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA

if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.util.profiler import Profiler
    from mglg.graphics.easing import *
    from math import sin
    import imgui

    win = Win(use_imgui=True)

    part = Particles(win, scale=0.4, lifespan_range=(0.5, 0.8), 
                     extent_range=(0.5, 1),
                     extent_ease=SMOOTHERSTEP,
                     initial_scale_range=(0.01, 0.01),
                     final_scale_range=(0.1, 0.4),
                     initial_red_range=(0.1, 0.1),
                     final_red_range=(0.8, 1),
                     final_green_range=(0.5, 0.1),
                     initial_alpha_range=(0, 1),
                     final_alpha_range=(1, 1),
                     alpha_ease=BOUNCE_IN_OUT,
                     scale_ease=BOUNCE_IN_OUT,
                     num_particles=1e4,
                     max_delay=0.5)

    prof = Profiler(gpu=True, ctx=win.ctx)
    prof.active = True

    counter = 0
    part.spawn(100)
    while not win.should_close:
        part.position.y = sin(counter/100)*0.1
        with prof:
            counter += 1
            if counter % 200 == 0:
                part.spawn(500)
                pass
            part.draw()
        imgui.new_frame()
        imgui.set_next_window_position(10, 10)
        imgui.set_next_window_size(270, 300)
        imgui.begin('stats (milliseconds)')
        imgui.text('Worst CPU: %f' % prof.worst_cpu)
        imgui.plot_lines('CPU', prof.cpubuffer,
                            scale_min=0, scale_max=2, graph_size=(180, 100))
        imgui.text('Worst GPU: %f' % prof.worst_gpu)
        imgui.plot_lines('GPU', prof.gpubuffer,
                            scale_min=0, scale_max=2, graph_size=(180, 100))
        imgui.end()
        win.flip()
