import numpy as np
import moderngl as mgl
from timeit import default_timer
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.particle import ParticleEmitter

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
    vec2 tmp = (vertices + pos) * g_scale * scale + g_pos;
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

class Particles(Drawable2D):
    def __init__(self, win, num_particles=1e4, *args, **kwargs):
        super().__init__(win, *args, **kwargs)
        ctx = win.ctx
        self.prog = ctx.program(vertex_shader=pvert, fragment_shader=pfrag)
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
        self.texture = ctx.texture(particle.shape[:2], 4, particle.view('u1'), dtype='f4')
        # access uniforms
        self.u_vp = self.prog['vp']
        self.u_g_pos = self.prog['g_pos']
        self.u_g_scale = self.prog['g_scale']

    def spawn(self, num_particles):
        self._emitter.spawn(num_particles)
        self.visible = True
    
    def draw(self):
        if self.visible:
            gpuview = self._emitter.update(1/144)
            # ideally I'd return the particle count too,
            # but it wasn't allowed by cython? So stored as
            # member of the emitter
            count = self._emitter.count
            if count > 0:
                # we have at least one particle
                self.texture.use()
                self.u_vp.write(self.win.vp)
                self.u_g_pos.write(self.position)
                self.u_g_scale.write(self.scale)
                self.particle_vbo.write(gpuview)
                win.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE
                self.vao.render(mgl.TRIANGLE_STRIP, instances=count)
                win.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA

if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.util.profiler import Profiler
    from mglg.graphics.easing import *
    import imgui

    win = Win(use_imgui=True)

    part = Particles(win, scale=1, lifespan_range=(0.2, 1), 
                     extent_range=(0.5, 1),
                     extent_ease=EXPONENTIAL_OUT,
                     initial_scale_range=(0.01, 0.01),
                     final_scale_range=(0.1, 0.05),
                     initial_red_range=(1, 1),
                     final_red_range=(0.1, 0.2),
                     final_green_range=(1, 1),
                     num_particles=1e4)

    prof = Profiler(gpu=True, ctx=win.ctx)
    prof.active = True

    counter = 0
    part.spawn(1000)
    while not win.should_close:
        with prof:
            counter += 1
            if counter % 200 == 0:
                part.spawn(1000)
                pass
            part.draw()
        imgui.new_frame()
        imgui.set_next_window_position(10, 10)
        imgui.set_next_window_size(270, 300)
        imgui.begin('stats (milliseconds)')
        imgui.text('Worst CPU: %f' % prof.worst_cpu)
        imgui.plot_lines('CPU', prof.cpubuffer,
                            scale_min=0, scale_max=30, graph_size=(180, 100))
        imgui.text('Worst GPU: %f' % prof.worst_gpu)
        imgui.plot_lines('GPU', prof.gpubuffer,
                            scale_min=0, scale_max=10, graph_size=(180, 100))
        imgui.end()
        win.flip()

