import imgui
import ctypes
import moderngl
import numpy as np

class ModernGLRenderer(object):
    # https://github.com/moderngl/moderngl-window/blob/master/moderngl_window/integrations/imgui.py#L81

    VERTEX_SHADER_SRC = """
        #version 330
        uniform mat4 ProjMtx;
        in vec2 Position;
        in vec2 UV;
        in vec4 Color;
        out vec2 Frag_UV;
        out vec4 Frag_Color;
        void main() {
            Frag_UV = UV;
            Frag_Color = Color;
            gl_Position = ProjMtx * vec4(Position.xy, 0, 1);
        }
    """
    FRAGMENT_SHADER_SRC = """
        #version 330
        uniform sampler2D Texture;
        in vec2 Frag_UV;
        in vec4 Frag_Color;
        out vec4 Out_Color;
        void main() {
            Out_Color = (Frag_Color * texture(Texture, Frag_UV.st));
        }
    """

    def __init__(self, win):
        self._prog = None
        self._fbo = None
        self._font_texture = None
        self._vertex_buffer = None
        self._index_buffer = None
        self._vao = None
        self.wnd = win
        self.ctx = self.wnd.ctx

        if not self.wnd:
            raise ValueError('Missing window reference')

        if not self.ctx:
            raise ValueError('Missing moderngl contex')

        if not imgui.get_current_context():
            raise RuntimeError(
                "No valid ImGui context. Use imgui.create_context() first and/or "
                "imgui.set_current_context()."
            )
        self.io = imgui.get_io()
        self._font_texture = None
        self.io.delta_time = 1.0 / 60.0
        self._create_device_objects()
        self.refresh_font_texture()

    def refresh_font_texture(self):
        width, height, pixels = self.io.fonts.get_tex_data_as_rgba32()

        if self._font_texture:
            self._font_texture.release()

        self._font_texture = self.ctx.texture((width, height), 4, data=pixels)
        self.io.fonts.texture_id = self._font_texture.glo
        self.io.fonts.clear_tex_data()

    def _create_device_objects(self):
        self._prog = self.ctx.program(
            vertex_shader=self.VERTEX_SHADER_SRC,
            fragment_shader=self.FRAGMENT_SHADER_SRC,
        )
        self.projMat = self._prog['ProjMtx']
        self._prog['Texture'].value = 0
        self._vertex_buffer = self.ctx.buffer(reserve=imgui.VERTEX_SIZE * 65536, dynamic=True)
        self._index_buffer = self.ctx.buffer(reserve=imgui.INDEX_SIZE * 65536, dynamic=True)
        self._vao = self.ctx.vertex_array(
            self._prog,
            [
                (self._vertex_buffer, '2f 2f 4f1', 'Position', 'UV', 'Color'),
            ],
            index_buffer=self._index_buffer,
            index_element_size=imgui.INDEX_SIZE,
        )

    def render(self, draw_data):
        io = self.io
        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_fb_scale[0])
        fb_height = int(display_height * io.display_fb_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        self.projMat.value = (
            2.0 / display_width, 0.0, 0.0, 0.0,
            0.0, 2.0 / -display_height, 0.0, 0.0,
            0.0, 0.0, -1.0, 0.0,
            -1.0, 1.0, 0.0, 1.0,
        )

        draw_data.scale_clip_rects(*io.display_fb_scale)

        self.ctx.enable_only(moderngl.BLEND)
        self.ctx.blend_equation = moderngl.FUNC_ADD
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        self._font_texture.use()

        for commands in draw_data.commands_lists:
            # Create a numpy array mapping the vertex and index buffer data without copying it
            vtx_type = ctypes.c_byte * commands.vtx_buffer_size * imgui.VERTEX_SIZE
            idx_type = ctypes.c_byte * commands.idx_buffer_size * imgui.INDEX_SIZE
            vtx_ptr = (vtx_type).from_address(commands.vtx_buffer_data)
            idx_ptr = (idx_type).from_address(commands.idx_buffer_data)
            self._vertex_buffer.write(vtx_ptr)
            self._index_buffer.write(idx_ptr)
            # vtx_ptr = ctypes.cast(commands.vtx_buffer_data, ctypes.POINTER(ctypes.c_byte))
            # idx_ptr = ctypes.cast(commands.idx_buffer_data, ctypes.POINTER(ctypes.c_byte))
            # vtx_data = np.ctypeslib.as_array(vtx_ptr, (commands.vtx_buffer_size * imgui.VERTEX_SIZE,))
            # idx_data = np.ctypeslib.as_array(idx_ptr, (commands.idx_buffer_size * imgui.INDEX_SIZE,))
            # self._vertex_buffer.write(vtx_data)
            # self._index_buffer.write(idx_data)

            idx_pos = 0
            for command in commands.commands:
                x, y, z, w = command.clip_rect
                self.ctx.scissor = int(x), int(fb_height - w), int(z - x), int(w - y)
                self._vao.render(moderngl.TRIANGLES, vertices=command.elem_count, first=idx_pos)
                idx_pos += command.elem_count

        self.ctx.scissor = None

    def _invalidate_device_objects(self):
        if self._font_texture:
            self._font_texture.release()
        if self._vertex_buffer:
            self._vertex_buffer.release()
        if self._index_buffer:
            self._index_buffer.release()
        if self._vao:
            self._vao.release()
        if self._prog:
            self._prog.release()

        self.io.fonts.texture_id = 0
        self._font_texture = None

    def shutdown(self):
        self._invalidate_device_objects()
