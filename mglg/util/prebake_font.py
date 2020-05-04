# utility to premake an atlas + glyph cache

import argparse
import os
import mglg
from mglg.graphics.font.font_manager import FontManager
from mglg.graphics.font.sdf_font import SDFFont
import inspect
from string import ascii_letters, digits, punctuation, whitespace
import pickle as pkl

ascii_alphanum = ascii_letters + digits + punctuation + whitespace
ascii_alphanum = ascii_alphanum + 'ÁÉÍÓÚÑÜáéíóúñü¿¡'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pre-pickle glyph cache')
    parser.add_argument('infile', type=str, help='path to ttf')
    args = parser.parse_args()

    infile = args.infile
    infile = os.path.join(os.getcwd(), infile)
    print(infile)
    noext = os.path.splitext(infile)[0]
    noext_nopath = os.path.basename(noext)
    
    mglg_path = os.path.dirname(inspect.getfile(mglg))
    cache_path = os.path.join(mglg_path, 'graphics', 'font', 'cache')
    if not os.path.exists(cache_path):
        os.mkdir(cache_path)
    out_path = os.path.join(cache_path, noext_nopath + '.pkl')

    manager = FontManager()
    atlas = manager.atlas_sdf
    fnt = SDFFont(infile, atlas)
    fnt.load(ascii_alphanum)

    with open(out_path, 'wb') as f:
        pkl.dump(atlas, f, protocol=4)
        pkl.dump(fnt.glyphs, f, protocol=4)

    with open(out_path, 'rb') as f:
        iatlas = pkl.load(f)
        iglyphs = pkl.load(f)
    print(iatlas.shape)
    print(out_path)