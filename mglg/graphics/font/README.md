Font-based stuff is based on the SDF implementation in glumpy.

A few issues:
  - I've added a pre-baking utility which produces pickled fonts and significantly improves startup time, but probably ruins the opportunity to mix in other fonts.
  - Does the atlas need to be 1024x1024 for our implementation? The pickled files are pretty large...
