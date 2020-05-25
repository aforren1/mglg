# utility to premake an atlas + glyph cache

import argparse
import os
import numpy as np
import mglg
from mglg.graphics.font.atlas import Atlas
from mglg.graphics.font.sdf_font import SDFFont
import inspect
from string import ascii_letters, digits, punctuation, whitespace
import pickle as pkl

ascii_alphanum = ascii_letters + digits + punctuation + whitespace
ascii_alphanum = ascii_alphanum + 'ÁÉÍÓÚÑÜáéíóúñü¿¡'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pre-pickle glyph cache')
    parser.add_argument('infile', type=str, help='path to ttf')
    parser.add_argument('outpath', type=str, help='relative path for output storage')
    parser.add_argument('--view', dest='view', default=False, action='store_true')
    args = parser.parse_args()

    infile = args.infile
    infile = os.path.join(os.getcwd(), infile)
    print('Input file: %s' % infile)
    noext = os.path.splitext(infile)[0]
    noext_nopath = os.path.basename(noext)
    
    cache_path = os.path.join(os.getcwd(), args.outpath)
    if not os.path.exists(cache_path):
        os.mkdir(cache_path)
    out_path = os.path.join(cache_path, noext_nopath + '.pklfont')
    print('Output path: %s' % out_path)

    atlas = np.zeros((512, 512), np.float32).view(Atlas)
    fnt = SDFFont(infile, atlas)
    fnt.load(ascii_alphanum)

    other = {'height': fnt.height, 'ascender': fnt.ascender,
             'descender': fnt.descender, 'linegap': fnt.linegap}

    # protocol 4 will work for all the Python 3 versions we 
    # care about, and is not too much slower than 5 for this problem
    if args.view:
        import matplotlib.pyplot as plt
        plt.imshow(atlas)
        plt.show()
    with open(out_path, 'wb') as f:
        pkl.dump(atlas, f, protocol=4)
        pkl.dump(fnt.glyphs, f, protocol=4)
        pkl.dump(other, f, protocol=4)
