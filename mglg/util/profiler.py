from timeit import default_timer
import numpy as np

class Profiler(object):
    __slots__ = ('active', 'gpuquery', 't0', 'cpubuffer', 'gpubuffer', 'counter', '_size')
    def __init__(self, gpu=False, ctx=None, buffer_size=100):
        self.active = False
        self.gpuquery = None
        if gpu and ctx is not None:
            self.gpuquery = ctx.query(time=True)
        self.cpubuffer = np.zeros(buffer_size, dtype='f4')
        self.gpubuffer = np.zeros(buffer_size, dtype='f4')
        self._size = buffer_size
        self.counter = 0

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
            self.cpubuffer[idx] = (t1 - self.t0) * 1000 # ms
            if self.gpuquery:
                self.gpubuffer[idx] = self.gpuquery.elapsed/1000000.0 # ms

    def __enter__(self):
        self.begin()
        return self
    
    def __exit__(self, *args):
        self.end()
