import atexit
import sys
from timeit import default_timer

import glfw
import moderngl as mgl
import glm
from mglg.math.vector import Vec4

if not glfw.init():
    raise ValueError('GLFW init went terribly wrong?')
atexit.register(glfw.terminate)


class Win(object):
    def __init__(self, vsync=1, screen=0):
        # TODO: multi-display with shared context
        # from psychopy & moderngl-window
        # fullscreen stuff-- always
        monitors = glfw.get_monitors()
        if len(monitors) < screen + 1:
            screen = 0  # default to screen 0 if no external monitors
        monitor = monitors[screen]
        video_mode = glfw.get_video_mode(monitor)

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
        glfw.window_hint(glfw.AUTO_ICONIFY, 0)

        self._win = glfw.create_window(width=self.width, height=self.height,
                                       title='', monitor=monitor, share=None)

        # Assumes that this will be the only context?
        glfw.make_context_current(self._win)
        glfw.swap_interval(bool(vsync))
        glfw.set_key_callback(self._win, self._on_key)
        glfw.set_cursor_pos_callback(self._win, self._on_cursor_move)
        # mouse initial pos in center of screen
        glfw.set_input_mode(self._win, glfw.CURSOR, glfw.CURSOR_HIDDEN)
        glfw.set_cursor_pos(self._win, self.width//2, self.height//2)
        if glfw.raw_mouse_motion_supported():
            glfw.set_input_mode(self._win, glfw.RAW_MOUSE_MOTION, True)
        self.mouse_pos = 0, 0

        # set up moderngl context
        major = glfw.get_window_attrib(self._win, glfw.CONTEXT_VERSION_MAJOR)
        minor = glfw.get_window_attrib(self._win, glfw.CONTEXT_VERSION_MINOR)

        self.ctx = mgl.create_context(require=int('%i%i0' % (major, minor)))
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self._clear_color = Vec4(0.3, 0.3, 0.3, 1)

        # other setup
        self.vp = glm.ortho(-0.5/(self.height/self.width),
                            0.5/(self.height/self.width), -0.5, 0.5)
        self.frame_rate = video_mode.refresh_rate
        self.frame_period = 1/self.frame_rate
        self.prev_time = default_timer()
        print(self.prev_time)
        self.dt = self.frame_period
        self.should_close = False
        self.ctx.clear(*self.clear_color)

    def _on_key(self, win_ptr, key, scancode, action, modifiers):
        if key == glfw.KEY_ESCAPE:
            self.should_close = True

    def _on_cursor_move(self, win_ptr, x, y):
        # transform to window coordinates
        # center
        x -= self.width / 2
        y -= self.height / 2
        # scale to window height
        x /= float(self.height)
        y /= float(-self.height)
        self.mouse_pos = x, y

    def flip(self):
        # glfw.make_context_current(self._win)
        glfw.swap_buffers(self._win)
        glfw.poll_events()
        self.ctx.clear(*self.clear_color)
        t1 = default_timer()
        self.dt = t1 - self.prev_time
        self.prev_time = t1

    def close(self):
        glfw.set_window_should_close(self._win, True)

    @property
    def clear_color(self):
        return self._clear_color

    @clear_color.setter
    def clear_color(self, val):
        self._clear_color.rgb = val


if __name__ == '__main__':
    from mglg.graphics.win import Win
    win = Win(screen=0, vsync=1)

    while not win.should_close:
        print(win.mouse_pos)
        win.flip()
    win.close()