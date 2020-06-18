#cython: boundscheck=False
#cython: nonecheck=False
#cython: wraparound=False
#cython: infertypes=True
#cython: initializedcheck=False
#cython: cdivision=True
import numpy as np
cimport numpy as np
from .easing import LINEAR, easings
from .easing cimport EaseFn, eases

cdef inline double lerp(const double v0, const double v1, const double t):
    return (1.0 - t) * v0 + t * v1

# this is CPU-side data, used to calculate data that ends
# up being sent to GPU
cdef packed struct cpu_particle_type:
    np.float32_t initial_angle
    np.float32_t extent
    np.float32_t final_position[2]
    np.float32_t initial_scale
    np.float32_t final_scale
    np.float32_t initial_color[4]
    np.float32_t final_color[4]
    np.float32_t lifespan
    np.float32_t current_time
    np.float32_t delay

cpu_dtype = np.dtype([('initial_angle', 'f'), # drawn from von mises
                      ('extent', 'f'), # drawn from uniform [min, max], where max is 1
                      ('final_position', '2f'), # calculated from two before
                      ('initial_scale', 'f'), # drawn from uniform [0, 1]
                      ('final_scale', 'f'), # drawn from uniform [0, 1]
                      ('initial_color', '4f'), # Each channel drawn from uniform [0, 1]
                      ('final_color', '4f'), # each channel drawn from uniform [0, 1]
                      ('lifespan', 'f'), # drawn from uniform [0, max_life]
                      # now intermediate stuff?
                      ('current_time', 'f'), # current time for this particle
                      ('delay', 'f')])

# this is data that actually goes to the GPU
# (calculated via CPU)
cdef packed struct gpu_particle_type:
    np.float32_t pos[2]
    np.float32_t scale
    np.float32_t color[4]

gpu_dtype = np.dtype([('pos', '2f'), ('scale', 'f'), ('color', '4f')])

# we'll allocate a max number of particles for one of the VBOs
# use instancing for the base vertices/texture UVs
# 
# TODO: extra flags so that if data hasn't changed/
# no alive particles, don't draw
# http://www.opengl-tutorial.org/intermediate-tutorials/billboards-particles/particles-instancing/
ctypedef (double, double) tf

cdef class ParticleEmitter:
    cdef cpu_particle_type[:] cpu_parts
    # gpu_particles gets copied out
    cdef gpu_particle_type[:] gpu_parts
    cdef int max_particles
    cdef int pending_emit
    cdef EaseFn extent_ease
    cdef EaseFn scale_ease
    cdef EaseFn color_ease
    cdef public int count
    cdef double max_life
    cdef double _pending_life

    def __init__(self, tf extent_range=(0.5, 1.0), int extent_ease=LINEAR,
                 tf initial_scale_range=(0.1, 0.05), tf final_scale_range=(0.05, 0.01),
                 int scale_ease=LINEAR,
                 tf initial_red_range=(0.9, 1), tf initial_green_range=(0.1, 0.15),
                 tf initial_blue_range=(0.1, 0.15), tf initial_alpha_range=(0.8, 1.0),
                 tf final_red_range=(0.9, 1), tf final_green_range=(0.1, 0.15),
                 tf final_blue_range=(0.1, 0.15), tf final_alpha_range=(0.4, 0.8),
                 int color_ease=LINEAR,
                 tf lifespan_range=(0.05, 0.5), int max_particles=1000, 
                 double max_delay=0.05, *args, **kwargs):
        # set up the RNG
        rng = np.random.default_rng()
        unif = rng.uniform
        mp = max_particles

        self.extent_ease = eases[extent_ease]
        self.scale_ease = eases[scale_ease]
        self.color_ease = eases[color_ease]
        self.max_particles = max_particles
        self.gpu_parts = np.empty(max_particles, dtype=gpu_dtype)
        cpup = np.empty(max_particles, dtype=cpu_dtype)

        # fill the cpu_particles
        cpup['initial_angle'][:] = unif(0, 6.28, mp)
        cpup['extent'][:] = unif(extent_range[0], extent_range[1], mp)
        cpup['final_position'][:, 0] = cpup['extent'] * np.cos(cpup['initial_angle'])
        cpup['final_position'][:, 1] = cpup['extent'] * np.sin(cpup['initial_angle'])
        cpup['initial_scale'][:] = unif(initial_scale_range[0], initial_scale_range[1], mp)
        cpup['final_scale'][:] = unif(final_scale_range[0], final_scale_range[1], mp)
        cpup['initial_color'][:, 0] = unif(initial_red_range[0], initial_red_range[1], mp)
        cpup['initial_color'][:, 1] = unif(initial_green_range[0], initial_green_range[1], mp)
        cpup['initial_color'][:, 2] = unif(initial_blue_range[0], initial_blue_range[1], mp)
        cpup['initial_color'][:, 3] = unif(initial_alpha_range[0], initial_alpha_range[1], mp)
        cpup['final_color'][:, 0] = unif(final_red_range[0], final_red_range[1], mp)
        cpup['final_color'][:, 1] = unif(final_green_range[0], final_green_range[1], mp)
        cpup['final_color'][:, 2] = unif(final_blue_range[0], final_blue_range[1], mp)
        cpup['final_color'][:, 3] = unif(final_alpha_range[0], final_alpha_range[1], mp)
        cpup['lifespan'][:] = unif(lifespan_range[0], lifespan_range[1], mp)
        cpup['current_time'][:] = cpup['lifespan'] + 0.1
        cpup['delay'][:] = unif(0, max_delay, mp)
        self.cpu_parts = cpup
        self.pending_emit = 0
        self.max_life = lifespan_range[1] + max_delay + 0.5
        self._pending_life = -1

    cpdef spawn(self, int num_particles):
        # generate N new particles
        # if we run over max_particles, start over from 0
        self.pending_emit += num_particles
        self._pending_life = self.max_life
    
    cpdef gpu_particle_type[:] update(self, const double dt):
        # update state of each particle,
        # exiting early if life < 0
        # do tweening, etc.
        # update particle_counter and gpu_particles
        # return slice of memoryview
        cdef int count = 0 # number of particles
        self._pending_life -= dt
        if self._pending_life < 0:
            self.count = 0
            self._pending_life = -1
            return self.gpu_parts[:count]
        cdef int i
        cdef cpu_particle_type *p
        cdef double time
        for i in range(self.max_particles):
            # TODO: way to make a reference to the struct
            p = &self.cpu_parts[i]
            p.current_time += dt
            if p.current_time < 0.0: # particle alive, but delayed
                continue
            elif 0.0 <= p.current_time <= p.lifespan: # particle currently alive
                # "ease"y
                time = 1.0 - ((p.lifespan - p.current_time)/p.lifespan)
                self.gpu_parts[count].pos[0] = lerp(0, p.final_position[0], 
                                                    self.extent_ease(time))
                self.gpu_parts[count].pos[1] = lerp(0, p.final_position[1],
                                                    self.extent_ease(time))
                self.gpu_parts[count].scale = lerp(p.initial_scale, p.final_scale, 
                                                self.scale_ease(time))
                self.gpu_parts[count].color[0] = lerp(p.initial_color[0], p.final_color[0], 
                                                    self.color_ease(time))
                self.gpu_parts[count].color[1] = lerp(p.initial_color[1], p.final_color[1], 
                                                    self.color_ease(time))
                self.gpu_parts[count].color[2] = lerp(p.initial_color[2], p.final_color[2], 
                                                    self.color_ease(time))
                self.gpu_parts[count].color[3] = lerp(p.initial_color[3], p.final_color[3], 
                                                    self.color_ease(time))
                count += 1
            else: # particle currently dead
                if self.pending_emit > 0:
                    self.pending_emit -= 1
                    self.gpu_parts[count].pos[0] = 0
                    self.gpu_parts[count].pos[1] = 0
                    self.gpu_parts[count].scale = p.initial_scale
                    self.gpu_parts[count].color[0] = p.initial_color[0]
                    self.gpu_parts[count].color[1] = p.initial_color[1]
                    self.gpu_parts[count].color[2] = p.initial_color[2]
                    self.gpu_parts[count].color[3] = p.initial_color[3]
                    p.current_time = -p.delay
                    count += 1
        self.count = count # current number of particles
        return self.gpu_parts[:count] # need to sanity check that there are any particles in the memoryview

