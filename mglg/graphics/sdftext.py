from string import ascii_letters, digits, punctuation, whitespace
import numpy as np
from numpy import float32, uint32

import moderngl as mgl
from mglg.math.vector import Vec4
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.font.font_manager import FontManager

vs = '''
#version 330
uniform mat4 mvp;

in vec2 vertices;
in vec2 texcoord;
out vec2 v_texcoord;

void main()
{
    gl_Position = mvp * vec4(vertices, 0.0, 1.0);
    v_texcoord = texcoord;
}
'''
# TODO: see https://github.com/libgdx/libgdx/wiki/Distance-field-fonts
fs = '''
#version 330
uniform vec4 fill_color;
uniform vec4 outline_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D atlas_data;
uniform float smoothness = 0.02;
uniform vec2 outline_range = vec2(0.5, 0.3);

in vec2 v_texcoord;
out vec4 f_color;

void main()
{
    float intensity = texture2D(atlas_data, v_texcoord).r;
    f_color = smoothstep(outline_range.x - smoothness, outline_range.x + smoothness, intensity) * fill_color;

    // outline
    if (outline_range.x > outline_range.y)
    {
        float mid = (outline_range.x + outline_range.y) * 0.5;
        float half_range = (outline_range.x - outline_range.y) * 0.5;
        f_color += smoothstep(half_range + smoothness, half_range - smoothness, distance(mid, intensity)) * outline_color;
    }
}

'''

sdf_shader = None
def SDFShader(context):
    global sdf_shader
    if sdf_shader is None:
        sdf_shader = context.program(vertex_shader=vs, fragment_shader=fs)
    return sdf_shader

class Text2D(Drawable2D):
    def __init__(self, window, text, font, 
                 fill_color=(0, 1, 0, 1), outline_color=(1, 1, 1, 1),
                 anchor_x='center', anchor_y='center', *args, **kwargs):
        super().__init__(window, *args, **kwargs)
        ctx = self.win.ctx
        self.shader = SDFShader(ctx)
        self._fill_color = Vec4(fill_color)
        self._outline_color = Vec4(outline_color)
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        fnt = FontManager.get(font, mode='sdf')
        self.font = fnt
        self._indexing = np.array([0, 1, 2, 0, 2, 3], dtype=uint32)
        vertices, indices = self.bake(text)
        manager = FontManager()
        atlas = manager.atlas_sdf
        self.atlas = ctx.texture(atlas.shape[0:2], 1, atlas.view(np.ubyte), dtype='f4')
        self.atlas.filter = (mgl.LINEAR, mgl.LINEAR)
        vbo = ctx.buffer(vertices)
        ibo = ctx.buffer(indices)
        self.vao = ctx.vertex_array(self.shader, [(vbo, '2f 2f', 'vertices', 'texcoord')],
                                    index_buffer=ibo)
        self.atlas.use()
        self.mvp_unif = self.shader['mvp']
        self.fill_unif = self.shader['fill_color']
        self.outline_unif = self.shader['outline_color']
    
    def draw(self):
        if self.visible:
            self.atlas.use()
            mvp = self.win.vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.fill_unif.write(self._fill_color)
            self.outline_unif.write(self._outline_color)
            self.vao.render(mgl.TRIANGLES)
    
    def bake(self, text):
        font = self.font
        anchor_x = self.anchor_x
        anchor_y = self.anchor_y
        n = len(text) - text.count('\n')
        indices = np.empty((n, 6), dtype=uint32)
        vertices = np.empty((n, 4), dtype=[('vertices', float32, 2),
                                           ('texcoord', float32, 2)])

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
                y0 = pen[1] + glyph.offset[1]
                x1 = x0 + glyph.shape[1]
                y1 = y0 - glyph.shape[0]
                u0, v0, u1, v1 = glyph.texcoords
                vertices[index]['vertices'] = ((x0, y0), (x0, y1),
                                               (x1, y1), (x1, y0))
                vertices[index]['texcoord'] = ((u0, v0), (u0, v1),
                                               (u1, v1), (u1, v0))
                indices[index] = index*4
                indices[index] += tmp
                pen[0] = pen[0]+glyph.advance[0] + kerning
                pen[1] = pen[1]+glyph.advance[1]
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
            vertices[start:end]['vertices'] += dx, 0

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
        vertices['vertices'] += 0, dy
        # make sure it's 1D
        vertices = vertices.ravel()
        # normalize to height (so vertices run from [-0.5, 0.5])
        tmp = vertices['vertices'][:, 1]
        mint = min(tmp)
        maxt = max(tmp)
        vertices['vertices'][...] = ((vertices['vertices'] - mint) / (maxt-mint)) - 0.5
        indices = indices.ravel()
        return vertices, indices


if __name__ == '__main__':
    import os.path as op
    from timeit import default_timer
    from mglg.graphics.win import Win
    from mglg.graphics.shape2d import Square
    from mglg.graphics.drawable import DrawableGroup
    from math import sin
    win = Win()

    font_path = op.join(op.dirname(__file__), '..', '..', 'examples', 'UbuntuMono-B.ttf')
    t0 = default_timer()
    bases = Text2D(win, scale=0.1, fill_color=(1, 0.1, 0.1, 1), position=(0, 0),
                   outline_color=(0.5, 0.5, 1, 0.8), text='Tengo un gatito pequeñito', 
                   font=font_path)
    print('startup time: %f' % (default_timer() - t0))

    sqr = Square(win, scale=0.1)

    txt = DrawableGroup([bases])
    for i in range(3000):
        #bases.rotation += 0.01
        bases.scale = 0.1 + sin(i/100) * 0.05 
        sqr.draw()
        txt.draw()
        win.flip()
        if win.should_close:
            break
        if win.dt > 0.02:
            print(win.dt)
    win.close()