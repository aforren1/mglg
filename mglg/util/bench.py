import timeit

# from https://github.com/mosra/magnum-bindings/blob/master/src/python/magnum/test/benchmark_math.py#L39

def timethat(expr, number=1e5, setup='pass', globs=None):
    title = expr
    print('{:40} {:8.5f} µs'.format(title, timeit.timeit(expr, number=int(number), globals=globs, setup=setup)*1000000.0/float(number)))
