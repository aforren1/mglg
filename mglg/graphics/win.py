import atexit
import sys
from timeit import default_timer

import glfw
import moderngl as mgl
import glm
from mglg.math.vector import Vec4
import imgui

from mglg.graphics.pyimgui.glfw_integration import GlfwRenderer


if not glfw.init():
    raise ValueError('GLFW init went terribly wrong?')
atexit.register(glfw.terminate)


class Win(object):
    def __init__(self, vsync=1, screen=0, timer=default_timer, use_imgui=False,
                 hidden=False):
        # TODO: multi-display with shared context
        # from psychopy & moderngl-window
        # fullscreen stuff-- always
        monitors = glfw.get_monitors()
        if len(monitors) < screen + 1:
            screen = 0  # default to screen 0 if no external monitors
        monitor = monitors[screen]
        video_mode = glfw.get_video_mode(monitor)
        self._monitor = monitor

        self.width, self.height = video_mode.size
        self.size = self.width, self.height

        # Configure the OpenGL context
        glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.NATIVE_CONTEXT_API)
        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, False)  # turn on for mac compat
        glfw.window_hint(glfw.RESIZABLE, False)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        glfw.window_hint(glfw.DEPTH_BITS, 0)  # 2d only?
        glfw.window_hint(glfw.SAMPLES, 8)  # MSAA
        glfw.window_hint(glfw.STENCIL_BITS, 0)  # no need for stencil buffer
        glfw.window_hint(glfw.REFRESH_RATE, video_mode.refresh_rate)
        glfw.window_hint(glfw.DECORATED, 0)  # no decorations allowed
        glfw.window_hint(glfw.STEREO, 0)
        glfw.window_hint(glfw.RED_BITS, video_mode.bits[0])
        glfw.window_hint(glfw.GREEN_BITS, video_mode.bits[1])
        glfw.window_hint(glfw.BLUE_BITS, video_mode.bits[2])
        glfw.window_hint(glfw.AUTO_ICONIFY, 1)
        glfw.window_hint(glfw.SRGB_CAPABLE, 1) # TODO: complete support

        if hidden:
            glfw.window_hint(glfw.VISIBLE, False)
            monitor = None
        self._win = glfw.create_window(width=self.width, height=self.height,
                                       title='', monitor=monitor, share=None)

        # Assumes that this will be the only context?
        glfw.make_context_current(self._win)
        glfw.swap_interval(bool(vsync))
        glfw.set_key_callback(self._win, self._on_key)
        # mouse initial pos in center of screen
        self.mouse_visible = True
        glfw.set_cursor_pos(self._win, self.width//2, self.height//2)
        # set up moderngl context
        major = glfw.get_window_attrib(self._win, glfw.CONTEXT_VERSION_MAJOR)
        minor = glfw.get_window_attrib(self._win, glfw.CONTEXT_VERSION_MINOR)

        self.ctx = mgl.create_context(require=int('%i%i0' % (major, minor)))
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.disable(mgl.DEPTH_TEST)
        self._clear_color = Vec4(0.5, 0.5, 0.5, 1)

        # other setup
        ratio = self.height/self.width
        self.vp = glm.ortho(-0.5/ratio, 0.5/ratio, -0.5, 0.5)
        self.frame_rate = video_mode.refresh_rate
        self.frame_period = 1/self.frame_rate
        self.timer = timer
        self.prev_time = self.timer()
        self.dt = self.frame_period
        self.should_close = False
        self.ctx.clear(*self.clear_color)

        self.use_imgui = use_imgui

        imgui.create_context()
        self.imrenderer = GlfwRenderer(self)


    def _on_key(self, win_ptr, key, scancode, action, modifiers):
        if key == glfw.KEY_ESCAPE:
            self.should_close = True

    def flip(self):
        if self.use_imgui:
            try:
                self.imrenderer.process_inputs()
                imgui.render()
                self.imrenderer.render(imgui.get_draw_data())
            except imgui.core.ImGuiError:
                pass
        glfw.poll_events()
        glfw.swap_buffers(self._win)
        self.ctx.clear(*self._clear_color)
        t1 = self.timer()
        self.dt = t1 - self.prev_time
        self.prev_time = t1

    def close(self):
        glfw.set_window_should_close(self._win, True)
    
    def show(self):
        glfw.show_window(self._win)
        # now make fullscreen
        glfw.set_window_monitor(self._win, self._monitor, 0, 0,
                                self.width, self.height, self.frame_rate)

    @property
    def clear_color(self):
        return self._clear_color

    @clear_color.setter
    def clear_color(self, val):
        self._clear_color.rgb = val

    @property
    def mouse_visible(self):
        return self._mouse_vis

    @mouse_visible.setter
    def mouse_visible(self, val):
        self._mouse_vis = bool(val)
        if val:
            glfw.set_input_mode(self._win, glfw.CURSOR, glfw.CURSOR_NORMAL)
        else:
            glfw.set_input_mode(self._win, glfw.CURSOR, glfw.CURSOR_HIDDEN)


if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.graphics.shapes import Rect
    from time import sleep
    win = Win(screen=1, vsync=1, use_imgui=True, hidden=True)

    rct = Rect(win, scale=0.1, fill_color=(.8, .3, .2, .5))

    sleep(2)
    win.show()

    counter = 0
    while not win.should_close:
        if win.use_imgui:
            imgui.new_frame()
            imgui.show_demo_window()
        counter += 1
        if counter % 1000 == 0:
            pass
            #win.should_close = True
            #win.use_imgui = not win.use_imgui
        rct.draw()
        win.flip()

        #print(win.dt)
    win.close()
