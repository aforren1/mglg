cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void mm44(const float[:, ::1] a,
                const float[:, ::1] b,
                float[:, ::1] out) nogil:
    cdef int i, j, k
    cdef int four = 4
    for i in range(four):
        for j in range(four):
            out[i, j] = 0.0
            for k in range(four):
                out[i, j] += a[i, k] * b[k, j]

