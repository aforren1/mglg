# cdefine the signature of our c function
#cython: boundscheck=False
#cython: nonecheck=False
#cython: initializedcheck=False
cdef extern from "sdf.h":
    void _compute_sdf(double *data, unsigned int width, unsigned int height)

# create the wrapper code, with numpy type annotations
cpdef void compute_sdf(double[:, ::1] in_array):
    """Compute the signed distance field"""
    cdef unsigned int w = in_array.shape[0]
    cdef unsigned int h = in_array.shape[1]
    _compute_sdf(&in_array[0, 0], h, w)

