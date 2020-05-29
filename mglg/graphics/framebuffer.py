import numpy as np
from mglg.graphics.drawable import Drawable2D
from mglg.graphics.image import ImageShader
from mglg.math import Vec4
from moderngl import TRIANGLE_STRIP, LINEAR
from glm import ortho

class Framebuffer(Drawable2D):
    vao = None

    def __init__(self, window, clear_color=None, alpha=1.0, *args, **kwargs):
        super().__init__(window, *args, **kwargs)
        ctx = window.ctx
        self.shader = ImageShader(ctx)
        self.texture = ctx.texture(ctx.screen.size, 4)
        self.texture.filter = (LINEAR, LINEAR)
        self.fbo = ctx.framebuffer(self.texture)

        cc = clear_color if clear_color else window.clear_color
        self._clear_color = Vec4(cc, 1.0)
        self.alpha = alpha
        self.mvp_unif = self.shader['mvp']
        self.alpha_unif = self.shader['alpha']
        ratio = self.scale.y / self.scale.x
        self.vp = ortho(-0.5/ratio, 0.5/ratio, -0.5, 0.5)

        if not self.vao:
            vertex_texcoord = np.empty(4, dtype=[('vertices', np.float32, 2),
                                                 ('texcoord', np.float32, 2)])
            vertex_texcoord['vertices'] = [(-0.5, -0.5), (0.5, -0.5),
                                           (-0.5, 0.5), (0.5, 0.5)]
            vertex_texcoord['texcoord'] = [(0, 0), (1, 0),
                                           (0, 1), (1, 1)]
            vbo = ctx.buffer(vertex_texcoord)
            self.set_vao(ctx, self.shader, vbo)

    def draw(self, vp=None):
        if self.visible:
            self.texture.use()
            vp = vp if vp else self.win.vp
            mvp = vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.alpha_unif.value = self.alpha
            self.vao.render(TRIANGLE_STRIP)

    @classmethod
    def set_vao(cls, context, shader, vbo):
        # re-use VAO
        cls.vao = context.simple_vertex_array(shader, vbo, 'vertices', 'texcoord')

    def use(self):
        self.fbo.clear(*self.clear_color)
        self.fbo.use()

    def unuse(self):
        self.win.ctx.screen.use()

    def __enter__(self):
        self.use()
        return self

    def __exit__(self, *args):
        self.unuse()

    @property
    def clear_color(self):
        return self._clear_color
    
    @clear_color.setter
    def clear_color(self, val):
        self._clear_color.rgb = val

if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.graphics.shapes import Circle
    from math import sin

    win = Win()
    cir = Circle(win, scale=0.1)

    tex = Framebuffer(win, (0, 0, 0), 0.5)
    tex.position.y += 0.1
    counter = 0
    while not win.should_close:
        counter += 1
        cir.position.x = sin(counter / 100) / 2
        with tex:
            cir.draw()
        cir.draw()
        tex.draw()
        win.flip()
