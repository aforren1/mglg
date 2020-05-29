import os.path as op
import numpy as np
from mglg.ext.stb_image import load
import moderngl as mgl
from mglg.graphics.drawable import Drawable2D
# avoid making new textures if we already have the exact texture
texture_cache = {}

image_vert = """
#version 330
uniform mat4 mvp; // depends on screen dims
in vec2 vertices;
in vec2 texcoord;
out vec2 v_texcoord;
void main()
{
    gl_Position = mvp * vec4(vertices, 0.0, 1.0);
    v_texcoord = texcoord;
}
"""

image_frag = """
#version 330
uniform sampler2D texture;
uniform float alpha;
in vec2 v_texcoord;
out vec4 f_color;
void main()
{
    f_color = texture2D(texture, v_texcoord) * alpha;
}

"""

image_shader = None
def ImageShader(context: mgl.Context):
    global image_shader
    if image_shader is None:
        image_shader = context.program(vertex_shader=image_vert, 
                                       fragment_shader=image_frag)
    return image_shader


class Image(Drawable2D):
    vao = None

    def __init__(self, window, image_path, alpha=1.0, *args, **kwargs):
        super().__init__(window, *args, **kwargs)
        context = window.ctx
        self.shader = ImageShader(context)
        bn = op.basename(image_path)
        if bn in texture_cache.keys():
            self.texture = texture_cache[bn]
        else:
            image = load(image_path)
            self.texture = context.texture(image.shape[0:2], 4, image)
            self.texture.filter = (mgl.LINEAR, mgl.LINEAR)
            texture_cache[bn] = self.texture
        self.alpha = alpha
        self.mvp_unif = self.shader['mvp']
        self.alpha_unif = self.shader['alpha']

        if self.vao is None:
            vertex_texcoord = np.empty(4, dtype=[('vertices', np.float32, 2),
                                                 ('texcoord', np.float32, 2)])
            vertex_texcoord['vertices'] = [(-0.5, -0.5), (-0.5, 0.5),
                                           (0.5, -0.5), (0.5, 0.5)]
            vertex_texcoord['texcoord'] = [(0, 1), (0, 0),
                                           (1, 1), (1, 0)]
            vbo = context.buffer(vertex_texcoord)
            self.set_vao(context, self.shader, vbo)

    def draw(self, vp=None):
        if self.visible:
            self.texture.use()
            vp = vp if vp else self.win.vp
            mvp = vp * self.model_matrix
            self.mvp_unif.write(mvp)
            self.alpha_unif.value = self.alpha
            self.vao.render(mgl.TRIANGLE_STRIP)

    @classmethod
    def set_vao(cls, context, shader, vbo):
        # re-use VAO
        cls.vao = context.simple_vertex_array(shader, vbo, 'vertices', 'texcoord')
