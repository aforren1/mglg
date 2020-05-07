
import numpy as np
cimport numpy as np

f4 = np.float32
# this is CPU-side data, used to calculate data that ends
# up being sent to GPU
cdef packed struct cpu_particle_type:
    np.float32_t initial_pos[2] # initial position
    np.float32_t initial_ang # initial launch angle
    np.float32_t initial_vel # magnitude of direction
    np.float32_t initial_color[4] # initial color (RGBA)
    np.float32_t final_color[4] # final color (RGBA)
    np.float32_t initial_life # lifespan [0, MAX]
    np.float32_t initial_scale # size of particle [0, ?]
    np.float32_t final_scale # size of particle [0, ?]

cpu_dtype = np.dtype([('initial_pos', 'f', 2), ('initial_ang', 'f'),
                      ('initial_vel', 'f'), ('initial_color', 'f', 4),
                      ('final_color', 'f', 4), ('initial_life', 'f'),
                      ('initial_scale', 'f'), ('final_scale', 'f')])

# position, angle, and velocity are enough to play out where
# the particle will be in space
# easing between initial & final color
# initial & final scale
# life continuously decreases (max depends on max time
# any particle should be alive)

# this is data that actually goes to the GPU
# (calculated via CPU)
cdef packed struct gpu_particle_type:
    np.float32_t pos[2]
    np.float32_t color[4]

# aim for ~1k particles?

# we'll allocate a max number of particles for one of the VBOs
# use instancing for the base vertices/texture UVs
# 

# gpu_particles is always transient
# particle_counter tells us number of instances and
# how far to look into the gpu_particles buffer, which
# can change every frame
# TODO: extra flags so that if data hasn't changed/
# no alive particles, don't draw
cdef class Particles:
    cdef cpu_particle_type[:] cpu_particles
    cdef gpu_particle_type[:] gpu_particles
    cdef int max_particles
    cdef int particle_counter
    cdef double max_life

    def __init__(self, int max_particles=1000, double max_life=0.5):
        self.max_particles = max_particles
        self.max_life = max_life
        self.particle_counter = 0
        self.cpu_particles = np.empty(max_particles, dtype=cpu_dtype)
        # need a dynamic VBO, IBO? for particles

    cpdef burst(self, int num_particles):
        # generate N new particles
        # if we run over max_particles, start over from 0
        pass
    
    cdef update(self):
        # update state of each particle,
        # exiting early if life < 0
        # do tweening, etc.
        # update particle_counter and gpu_particles
        # return slice of memoryview
        pass
    
    cpdef foo(self):
        return self.cpu_particles[:2]
