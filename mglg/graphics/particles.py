import numpy as np
import moderngl as mgl
from timeit import default_timer
from mglg.graphics.drawable import Drawable2D
from .particle import ParticleEmitter

class Particles(Drawable2D):
    def __init__(self, win, num_particles=1e4, *args, **kwargs):
        super().__init__(win, *args, **kwargs)
        ctx = win.ctx
        self._emitter = ParticleEmitter(max_particles=num_particles)
        self.visible = False
        self.particle_vbo = ctx.buffer(dynamic=True, reserve=28*num_particles)
        # shared data
        vt = np.empty(4, dtype=[('vertices', '2f4'), ('texcoord', '2f4')])
        vt['vertices'] = [(-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]
        vt['texcoord'] = [(0, 1), (0, 0), (1, 1), (1, 0)]
        vbo = ctx.buffer(vt.view(np.ubyte))
        self.vao = ctx.vertex_array(
            self.prog,
            [(vbo, '2f 2f', 'vertices', 'texcoord'),
             (self.particle_vbo, '2f 1f 4f /i', 'pos', 'scale', 'color')]
        )


    def spawn(self, num_particles):
        self._emitter.spawn(num_particles)
        self.visible = True
    
    def draw(self):
        if self.visible:
            gpuview = self._emitter.update(1/60)
            if self.count > 0:
                # we have at least one particle
