from timeit import default_timer
import numpy as np

class Profiler(object):
    __slots__ = ('active', 'gpuquery', 't0', 'cpubuffer', 'gpubuffer', 'counter', '_size',
                 'worst_cpu', 'worst_gpu')
    def __init__(self, gpu=False, ctx=None, buffer_size=200):
        self.active = False
        self.gpuquery = None
        if gpu and ctx is not None:
            self.gpuquery = ctx.query(time=True)
        self.cpubuffer = np.zeros(buffer_size, dtype='f4')
        self.gpubuffer = np.zeros(buffer_size, dtype='f4')
        self._size = buffer_size
        self.counter = 0
        self.worst_cpu = 0
        self.worst_gpu = 0

    def begin(self):
        if self.active:
            if self.gpuquery:
                self.gpuquery.mglo.begin()
        self.t0 = default_timer()
    
    def end(self):
        t1 = default_timer()
        if self.active:
            if self.gpuquery:
                self.gpuquery.mglo.end()
            idx = -1
            if self.counter >= self._size:
                self.cpubuffer[:-1] = self.cpubuffer[1:]
                self.gpubuffer[:-1] = self.gpubuffer[1:]
            else:
                idx = self.counter
                self.counter += 1
                self.worst_gpu = 0
                self.worst_cpu = 0
            cpu_time = (t1 - self.t0) * 1000 # ms
            self.cpubuffer[idx] = cpu_time
            self.worst_cpu = cpu_time if cpu_time > self.worst_cpu else self.worst_cpu 
            if self.gpuquery:
                gpu_time = self.gpuquery.elapsed/1000000.0 # ms
                self.gpubuffer[idx] = gpu_time
                self.worst_gpu = gpu_time if gpu_time > self.worst_gpu else self.worst_gpu


    def __enter__(self):
        self.begin()
        return self
    
    def __exit__(self, *args):
        self.end()
