# -----------------------------------------------------------------------------
# Copyright (c) 2009-2016 Nicolas P. Rougier. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
""" Font Manager """
import os
import numpy as np
from . atlas import Atlas
from .sdf_font import SDFFont
import importlib.resources as pkg_resources
import pickle as pkl

class FontManager(object):
    """
    Font Manager

    The Font manager takes care of caching already loaded font. Currently, the only
    way to get a font is to get it via its filename.
    """

    # Default atlas
    _atlas_sdf = None

    # Font cache
    _cache_sdf = {}

    # The singleton instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def get(cls, filename):
        """
        Get a font from the cache, the local data directory or the distant server
        (in that order).
        """

        basename = os.path.basename(filename)
        barename = os.path.splitext(basename)[0]
        pklname = barename + '.pkl'
        glyphs = None
        try:
            with pkg_resources.open_binary('mglg.graphics.font.cache', pklname) as f:
                FontManager._atlas_sdf = pkl.load(f)
                glyphs = pkl.load(f)
        except FileNotFoundError:
            print('no exist')

        key = '%s' % (basename)
        if FontManager._atlas_sdf is None:
            FontManager._atlas_sdf = np.zeros((1024, 1024), np.float32).view(Atlas)
        atlas = FontManager._atlas_sdf
        cache = FontManager._cache_sdf

        if key not in cache.keys():
            cache[key] = SDFFont(filename, atlas)
        
        if glyphs is not None:
            cache[key].glyphs = glyphs

        return cache[key]

    @property
    def atlas_sdf(self):
        if FontManager._atlas_sdf is None:
            FontManager._atlas_sdf = np.zeros((1024, 1024), np.float32).view(Atlas)
        return FontManager._atlas_sdf
