import numpy as np
from math import sqrt

def fastnorm(val):
    return val / sqrt(val[0]**2 + val[1]**2)

def compute_miter(line_a, line_b, half_thick):
    tangent = fastnorm(line_a + line_b)
    miter = -tangent[1], tangent[0]
    tmp = np.array([-line_a[1], line_a[0]])
    return miter, half_thick / np.dot(miter, tmp)

def direction(a, b):
    # we're only doing the scalar ones for now, so don't bother 
    # using numpy fns
    return fastnorm(a - b)

def normal(dir):
    return -dir[1], dir[0]

# usage:

# path is [[x1, y1], [x2, y2], [x3, y3]]
# aka the outline
# number of "normals" (from getNormals) should match the number of vertices
# for closed shapes, they just add the initial vertex to the end

def get_normals(points, closed=True):
    # closed points should be in CW order
    # points is the outline/such of the thing, closed is whether the shape is closed

    # part 1: do polyline-normals
    # https://github.com/mattdesl/polyline-normals/blob/master/index.js
    points = np.array(points)
    if closed:
        points = np.vstack((points, points[0]))
    
    out = [] # [[normal[0], normal[1]], miter length (== miter in the final data)]

    total = len(points)
    for i in range(1, total):
        last = points[i-1]
        cur = points[i]
        nex = points[i+1] if i < (total-1) else None
        line_a = direction(cur, last)

        cur_normal = normal(line_a)
        if i == 1: # add initial normals
            out.append([cur_normal, 1])
        
        if nex is None: # no miter, simple segment
            out.append([cur_normal, 1])
        else:
            line_b = direction(nex, cur)
            miter, miter_len = compute_miter(line_a, line_b, 1)
            out.append([miter, miter_len])
    
    # if this polyline is a closed loop, clean up the last normal
    if total > 2 and closed:
        last = points[total-2]
        cur = points[0]
        nex = points[1]
        line_a = direction(cur, last)
        line_b = direction(nex, cur)

        miter, miter_len = compute_miter(line_a, line_b, 1)
        out[0] = miter, miter_len
        out[total-1] = miter, miter_len
        out.pop()
    
    return out


def generate_outline(points, closed):
    # now we start packing into a buffer
    # a la https://github.com/mattdesl/three-line-2d/blob/c0da016db3fcf9e9a6ebef8063fd7e8334af0ace/index.js
    normals = get_normals(points, closed)
    points = np.array(points)
    # I'm a little confused by this bit, but it's what the man says
    if closed:
        points = np.vstack((points, points[0]))
        normals.append(normals[0])
    index_count = max(0, len(points) * 6) # TODO: should be (len(points) - 1) * 6, but then loop fails
    count = 2 * len(points) # total number of vertices
    verts = np.empty(count, dtype=[('vertices', 'f4', 2), ('normal', 'f4', 2), ('miter', 'f4'), ('outer', 'i4')])
    inds = np.empty(index_count, dtype='i4')

    index = 0
    c = 0
    # organizing so it goes outer, inner, outer, inner, ...
    for p, n in zip(points, normals):
        i = index
        # we want the provoking vertex to always be the last one of the triangle
        # *and* be on the outside
        inds[c:c+6] = i, i+1, i+2, i+1, i+3, i+2
        c += 6
        verts[index:index+2]['vertices'] = p
        verts[index:index+2]['normal'] = n[0]
        verts[index:index+2]['miter'] = n[1], -n[1] # is this right?
        verts[index:index+2]['outer'] = 1, 0
        index += 2
        # skipping distance for now (not sure what that's setting)
    
    # TODO: I have no idea why the number of indices isn't right
    return verts, inds[:-6]
        
