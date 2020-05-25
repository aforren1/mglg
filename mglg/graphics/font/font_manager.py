# -----------------------------------------------------------------------------
# Copyright (c) 2009-2016 Nicolas P. Rougier. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
""" Font Manager """
import os
import numpy as np
from . atlas import Atlas
from .sdf_font import SDFFont
import pickle as pkl

class FontManager(object):
    """
    Font Manager

    The Font manager takes care of caching already loaded font. Currently, the only
    way to get a font is to get it via its filename.
    """

    # Font cache
    _cache_sdf = {}

    # The singleton instance
    _instance = None

    atlas_dim = 512

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
        glyphs = None
        other = None
        atlas = np.zeros((cls.atlas_dim, cls.atlas_dim), np.float32).view(Atlas)
        if os.path.splitext(filename)[1] == '.pklfont':
            with open(filename, 'rb') as f:
                atlas = pkl.load(f)
                glyphs = pkl.load(f)
                other = pkl.load(f)

        key = '%s' % (basename)
        cache = FontManager._cache_sdf

        if key not in cache.keys():
            cache[key] = SDFFont(filename, atlas)
        
        if glyphs is not None:
            cache[key].glyphs = glyphs
        
        if other is not None:
            cache[key].ascender = other['ascender']
            cache[key].descender = other['descender']
            cache[key].height = other['height']
            cache[key].linegap = other['linegap']

        return cache[key]
