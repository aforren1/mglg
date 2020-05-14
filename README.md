Built-for-purpose, minimal 2D graphics library.

Working on documentation, but the file [examples/jamboree.py](https://github.com/aforren1/mglg/blob/master/examples/jamboree.py) is pretty comprehensive.

To pre-create the glyphs and atlas, there's a command line tool, e.g.:

```bash
python mglg\util\prebake_font.py examples\UbuntuMono-B.ttf fonts\
```

Subsequent use of that font will instead load the pickled version (stored in mglg/graphics/font/cache), which is significantly faster. Note this only works for the SDF text (which I'll switch entirely over to soon).
