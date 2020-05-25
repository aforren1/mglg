# cython: c_string_type=unicode, c_string_encoding=ascii
import numpy as np
cimport numpy as np

cdef extern from "defs.h":
    pass

cdef extern from "stb_image.h":
    unsigned char* stbi_load(const char* filename, int *x, int *y, int *channels_in_file, int desired_channels)

cdef extern from "numpy/arrayobject.h":
    void PyArray_ENABLEFLAGS(np.ndarray arr, int flags)

cpdef load(const char* filename):
    cdef int x, y, channels_in_file, size
    cdef np.ndarray[np.uint8_t, ndim=3] arr
    cdef unsigned char* data = stbi_load(filename, &x, &y, &channels_in_file, 0)
    if data is NULL:
        raise ValueError('File failed to load.')
    cdef np.npy_intp *dims = [x, y, channels_in_file]
    arr = np.PyArray_SimpleNewFromData(3, dims, np.NPY_UINT8, data)
    PyArray_ENABLEFLAGS(arr, np.NPY_ARRAY_OWNDATA)
    return arr
