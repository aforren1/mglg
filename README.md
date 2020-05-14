Built-for-purpose, minimal 2D graphics library.

Working on documentation, but the file [examples/jamboree.py](https://github.com/aforren1/mglg/blob/master/examples/jamboree.py) is pretty comprehensive.

To pre-create the glyphs and atlas, there's a command line tool, e.g.:

```bash
python -m mglg.util.prebake_font examples\UbuntuMono-B.ttf fonts\
```

Which saves a pickled file (in this case, `fonts\UbuntuMono-B.pklfont`) that includes the atlas, glyphs, and other info to avoid touching the font file.
