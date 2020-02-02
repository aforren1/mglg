from string import ascii_letters, digits, punctuation, whitespace
import numpy as np
from numpy import float32, uint32

import moderngl as mgl
from mglg.math.vector import Vec4
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.font.font_manager import FontManager
from mglg.graphics.shaders import TextShader

ascii_alphanum = ascii_letters + digits + punctuation + whitespace


class Text2D(Drawable2D):
    def __init__(self, window, text, font, color=(1, 1, 1, 1),
                 anchor_x='center', anchor_y='center', font_size=128, *args, **kwargs):
        super().__init__(window, *args, **kwargs)
        context = self.win.ctx
        width, height = self.win.size
        self.shader = TextShader(context)
        self._color = Vec4(color)
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        fnt = FontManager.get(font, font_size)
        self.font = fnt
        self._indexing = np.array([0, 1, 2, 0, 2, 3], dtype=uint32)
        vertices, indices = self.bake(text)
        manager = FontManager()
        atlas = manager.atlas_agg
        self.atlas = context.texture(atlas.shape[0:2], 3, atlas.view(np.ubyte))
        vbo = context.buffer(vertices)
        ibo = context.buffer(indices)
        self.vao = context.vertex_array(self.shader,
                                        [   # TODO: pad? maybe doesn't matter 'cause we're not streaming
                                            (vbo, '2f 2f 1f', 'vertices', 'texcoord', 'offset')
                                        ],
                                        index_buffer=ibo)

        self.shader['viewport'].value = width, height
        self.atlas.use()
        self.mvp_unif = self.shader['mvp']
        self.color_unif = self.shader['color']

    def draw(self):
        if self.visible:
            self.atlas.use()
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.color_unif.write(self._color)
            self.vao.render(mgl.TRIANGLES)

    def bake(self, text):
        font = self.font
        anchor_x = self.anchor_x
        anchor_y = self.anchor_y
        n = len(text) - text.count('\n')
        indices = np.empty((n, 6), dtype=uint32)
        vertices = np.empty((n, 4), dtype=[('vertices', float32, 2),
                                           ('texcoord', float32, 2),
                                           ('offset', float32)])

        start = 0
        pen = [0, 0]
        prev = None
        lines = []
        text_width, text_height = 0, 0
        # text is in pixels,
        # position is defining little boxes that texture will go into
        # texcoord defines the local texture location (not sure I get the units?)
        # offset is the offset of the texture??

        index = 0
        tmp = self._indexing
        for charcode in text:
            if charcode == '\n':
                prev = None
                lines.append(((start, index), pen[0]))
                start = index
                text_width = max(text_width, pen[0])
                pen[1] -= font.height
                pen[0] = 0
            else:
                glyph = font[charcode]
                kerning = glyph.get_kerning(prev)
                x0 = pen[0] + glyph.offset[0] + kerning
                offset = x0-int(x0)
                x0 = int(x0)
                y0 = pen[1] + glyph.offset[1]
                x1 = x0 + glyph.shape[0]
                y1 = y0 - glyph.shape[1]
                u0, v0, u1, v1 = glyph.texcoords
                vertices[index]['vertices'] = ((x0, y0), (x0, y1),
                                               (x1, y1), (x1, y0))
                vertices[index]['texcoord'] = ((u0, v0), (u0, v1),
                                               (u1, v1), (u1, v0))
                vertices[index]['offset'] = offset
                indices[index] = index*4
                indices[index] += tmp
                pen[0] = pen[0]+glyph.advance[0]/64. + kerning
                pen[1] = pen[1]+glyph.advance[1]/64.
                prev = charcode
                index += 1

        # now we have positions, etc. in pixels
        lines.append(((start, index+1), pen[0]))
        text_height = (len(lines)-1)*font.height
        text_width = max(text_width, pen[0])

        # Adjusting each line
        # center each line on x
        for ((start, end), width) in lines:
            if anchor_x == 'right':
                dx = -width/1.0
            elif anchor_x == 'center':
                dx = -width/2.0
            else:
                dx = 0
            vertices[start:end]['vertices'] += round(dx), 0

        # Adjusting whole label
        # same: adjust so that pixel-coordinate vertices are centered
        if anchor_y == 'top':
            dy = - (font.ascender + font.descender)
        elif anchor_y == 'center':
            dy = (text_height - (font.descender + font.ascender))/2
        elif anchor_y == 'bottom':
            dy = -font.descender + text_height
        else:
            dy = 0
        vertices['vertices'] += 0, round(dy)
        # make sure it's 1D
        vertices = vertices.ravel()
        # normalize to height (so vertices run from [-0.5, 0.5])
        tmp = vertices['vertices'][:, 1]
        mint = min(tmp)
        maxt = max(tmp)
        vertices['vertices'][...] = ((vertices['vertices'] - mint) / (maxt-mint)) - 0.5
        indices = indices.ravel()
        return vertices, indices

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color.rgba = color


class DynamicText2D(Text2D):
    def __init__(self, window, text='', font=None,
                 color=(1, 1, 1, 1), anchor_x='center',
                 anchor_y='center', font_size=128, expected_chars=300,
                 prefetch=ascii_alphanum, *args, **kwargs):
        super(Drawable2D, self).__init__(window, *args, **kwargs)
        ctx = self.win.ctx
        width, height = self.win.size
        self.shader = TextShader(ctx)
        self._color = Vec4(color)
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        fnt = FontManager.get(font, font_size)
        self.font = fnt
        manager = FontManager()
        self.prefetch(prefetch + text)
        atlas = manager.atlas_agg
        self.atlas = ctx.texture(atlas.shape[0:2], 3, atlas.view(np.ubyte))
        n = expected_chars * 10  # reserve 10x
        vert_bytes = n * 4 * 5 * 4  # chars x verts per char x floats per vert x bytes per float
        ind_bytes = n * 6 * 4
        self.vbo = ctx.buffer(reserve=vert_bytes, dynamic=True)
        self.ibo = ctx.buffer(reserve=ind_bytes, dynamic=True)
        self.vao = ctx.vertex_array(self.shader,
                                    [   # TODO: pad? we're streaming here
                                        (self.vbo, '2f 2f 1f', 'vertices', 'texcoord', 'offset')
                                    ],
                                    index_buffer=self.ibo)
        self._indexing = np.array([0, 1, 2, 0, 2, 3], dtype=uint32)
        self._text = ''
        if text != '':
            self.text = text
        self.shader['viewport'].value = width, height
        self.atlas.use()
        self.mvp_unif = self.shader['mvp']
        self.color_unif = self.shader['color']

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_txt):
        if new_txt != self._text:
            vertices, indices = self.bake(new_txt)
            self.num_vertices = indices.shape[0]
            self.vbo.orphan()
            self.ibo.orphan()
            self.vbo.write(vertices)
            self.ibo.write(indices)
            self._text = new_txt

    def draw(self):
        if self.visible and self._text != '':
            self.atlas.use()
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.color_unif.write(self._color)
            self.vao.render(mode=mgl.TRIANGLES, vertices=self.num_vertices)

    def prefetch(self, chars):
        # store these
        for charcode in chars:
            if charcode != '\n':
                x = self.font[charcode]


if __name__ == '__main__':
    import os.path as op
    from timeit import default_timer
    from mglg.graphics.win import Win
    from mglg.graphics.drawable import DrawableGroup
    win = Win()

    font_path = op.join(op.dirname(__file__), '..', '..', 'examples', 'UbuntuMono-B.ttf')

    t0 = default_timer()
    bases2 = Text2D(win, scale=(0.05, 0.05), color=(0.1, 1, 0.1, 1),
                    text='1234567890', font=font_path, position=(-0.4, 0), rotation=90, font_size=128)
    bases = Text2D(win, scale=(0.1, 0.1), color=(1, 0.1, 0.1, 0.7),
                   text='Tengo un gatito pequeñito', font=font_path, position=(0, -0.4), font_size=128)

    foobar = '┻━┻︵ \(°□°)/ ︵ ┻━┻'
    countup = DynamicText2D(win, text='123', scale=0.1, expected_chars=20,
                            font=font_path, position=(0, 0), font_size=32,
                            prefetch='0123456789' + foobar)
    print('startup time: %f' % (default_timer() - t0))
    # countup.prefetch('0123456789')

    txt = DrawableGroup([bases, countup, bases2])
    counter = 0
    for i in range(1200):
        counter += 12
        if counter % 96 == 0:
            countup.text = foobar
        else:
            countup.text = str(counter)
        txt.draw()
        win.flip()
        if win.should_close:
            break
        if win.dt > 0.02:
            print(win.dt)

    win.close()
