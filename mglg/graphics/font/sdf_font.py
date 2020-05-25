import os.path
import numpy as np
from . glyph import Glyph
from mglg.ext.sdf import compute_sdf

try:
    import freetype
except ImportError:
    pass
# derived from
# https://github.com/glumpy/glumpy/blob/c50daeca5b3f99161992062f771705be9b47f428/glumpy/graphics/text/sdf_font.py
def bilinear_interpolate(im, x, y):
    """ By Alex Flint on StackOverflow """
    x0 = x.astype(np.int32)
    x1 = x0 + 1
    y0 = y.astype(np.int32)
    y1 = y0 + 1

    x0 = np.clip(x0, 0, im.shape[1]-1)
    x1 = np.clip(x1, 0, im.shape[1]-1)
    y0 = np.clip(y0, 0, im.shape[0]-1)
    y1 = np.clip(y1, 0, im.shape[0]-1)

    Ia = im[ y0, x0 ]
    Ib = im[ y1, x0 ]
    Ic = im[ y0, x1 ]
    Id = im[ y1, x1 ]

    wa = (x1-x) * (y1-y)
    wb = (x1-x) * (y-y0)
    wc = (x-x0) * (y1-y)
    wd = (x-x0) * (y-y0)

    return wa*Ia + wb*Ib + wc*Ic + wd*Id

def zoom(Z, ratio):
    """ Bilinear image zoom """

    nrows, ncols = Z.shape
    x,y = np.meshgrid(np.linspace(0, ncols, int(ratio*ncols), endpoint=False),
                      np.linspace(0, nrows, int(ratio*nrows), endpoint=False))
    return bilinear_interpolate(Z, x, y)

class SDFFont(object):

    def __init__(self, filename, atlas):
        self._hires_size = 256
        self._lowres_size = 48
        self._padding = 0.125
        self.filename = filename
        self.atlas = atlas
        self.glyphs = {}
        self.is_pickled = False
        if os.path.splitext(filename)[1] != '.pklfont':
            face = freetype.Face(self.filename)
            face.set_char_size(self._lowres_size*64)
            metrics = face.size
            self.ascender  = metrics.ascender/64.0
            self.descender = metrics.descender/64.0
            self.height    = metrics.height/64.0
            self.linegap   = (self.height - self.ascender + self.descender)
        else: # it's a pickled file, so we'll fill in details from outside
            self.ascender = None
            self.descender = None
            self.height = None
            self.linegap = None
            self.is_pickled = True

    def __getitem__(self, charcode):
        if charcode not in self.glyphs.keys():
            self.load('%c' % charcode)
        return self.glyphs[charcode]
    
    def load_glyph(self, face, charcode):
        face.set_char_size( self._hires_size*64 )
        face.load_char(charcode, freetype.FT_LOAD_RENDER |
                                 freetype.FT_LOAD_NO_HINTING |
                                 freetype.FT_LOAD_NO_AUTOHINT)

        bitmap = face.glyph.bitmap
        width  = bitmap.width
        height = bitmap.rows
        pitch  = bitmap.pitch
        glyph = face.glyph
        bit_left = glyph.bitmap_left
        bit_top = glyph.bitmap_top
        ax = glyph.advance.x
        ay = glyph.advance.y

        # Get glyph into a numpy array
        G = np.array(bitmap.buffer).reshape(height,pitch)
        G = G[:,:width].astype(np.ubyte)

        # Pad high resolution glyph with a blank border and normalize values
        # between 0 and 1
        hires_width  = int((1+2*self._padding)*width)
        hires_height = int((1+2*self._padding)*height)
        hires_data = np.zeros((hires_height,hires_width), np.double)
        ox,oy = int(self._padding*width), int(self._padding*height)
        hires_data[oy:oy+height, ox:ox+width] = G/255.0

        # Compute distance field at high resolution
        if hires_width != 0:
            compute_sdf(hires_data)

        # Scale down glyph to low resolution size
        ratio = self._lowres_size/float(self._hires_size)
        # lowres_data = 1 - zoom(hires_data, ratio, cval=1.0)
        lowres_data = 1 - zoom(hires_data, ratio)

       # Compute information at low resolution size
        # size   = ( lowres_data.shape[1], lowres_data.shape[0] )
        offset = ((bit_left - self._padding*width) * ratio,
                  (bit_top + self._padding*height) * ratio)
        advance = ((ax/64.0)*ratio,
                   (ay/64.0)*ratio)
        return lowres_data, offset, advance

    def load(self, charcodes = ''):
        if self.is_pickled:
            return # using a cached font, so we don't have the original ttf
        face = freetype.Face(self.filename)
        for charcode in charcodes:
            if charcode in self.glyphs.keys():
                continue

            data ,offset, advance = self.load_glyph(face, charcode)

            h, w = data.shape
            region = self.atlas.allocate((h+2,w+2))
            if region is None:
                print("Cannot store glyph '%c'" % charcode)
                continue
            x, y, _, _ = region
            x, y = x+1, y+1
            self.atlas[y:y+h, x:x+w] = data.reshape(h, w)

            u0 = (x + 0.0)/float(self.atlas.shape[0])
            v0 = (y + 0.0)/float(self.atlas.shape[1])
            u1 = (x + w - 0.0)/float(self.atlas.shape[0])
            v1 = (y + h - 0.0)/float(self.atlas.shape[1])
            texcoords = (u0, v0, u1, v1)
            glyph = Glyph(charcode, data.shape, offset, advance, texcoords)
            self.glyphs[charcode] = glyph

            # Generate kerning (for reference size)
            face.set_char_size(self._lowres_size*64)
            for g in self.glyphs.values():
                kerning = face.get_kerning(g.charcode, charcode,
                                           mode=freetype.FT_KERNING_UNFITTED)
                if kerning.x != 0:
                    glyph.kerning[g.charcode] = kerning.x/64.0
                kerning = face.get_kerning(charcode, g.charcode,
                                           mode=freetype.FT_KERNING_UNFITTED)
                if kerning.x != 0:
                    g.kerning[charcode] = kerning.x/64.0