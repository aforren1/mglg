from timeit import default_timer
import numpy as np

class Profiler(object):
    __slots__ = ('active', 'gpuquery', 't0', 'buffer', 'counter')
    def __init__(self, gpu=False, ctx=None, buffer_size=100):
        self.active = False
        self.gpuquery = None
        if gpu and ctx is not None:
            self.gpuquery = ctx.query(time=True)
        self.buffer = np.zeros(buffer_size, dtype=[('cpu', np.float64), ('gpu', np.float64)])
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
            if self.counter >= self.buffer.shape[0]:
                self.buffer[:-1] = self.buffer[1:]
            else:
                idx = self.counter
                self.counter += 1
            self.buffer[idx]['cpu'] = t1 - self.t0
            if self.gpuquery:
                self.buffer[idx]['gpu'] = self.gpuquery.elapsed/1000000.0 # millis

    def __enter__(self):
        self.begin()
        return self
    
    def __exit__(self, *args):
        self.end()
