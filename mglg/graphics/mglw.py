import logging
import moderngl as mgl
from moderngl_window.context.base import WindowConfig
import moderngl_window as mglw
import glm
from timeit import default_timer
try:
    import imgui
    imgui.create_context()
    from moderngl_window.integrations.imgui import ModernglWindowRenderer
    has_imgui = True
except ImportError:
    has_imgui = False

# logger = logging.getLogger(__name__)

if has_imgui:
    class MglRenderer(ModernglWindowRenderer):
        def __enter__(self):
            imgui.new_frame()

        def __exit__(self, *args):
            imgui.render()
            self.render(imgui.get_draw_data())


def flip(self):
    self.swap_buffers()
    self.clear(*self.clear_color)
    t1 = default_timer()
    self.dt = t1 - self.t0
    self.t0 = t1


class BaseWin(mglw.WindowConfig):
    gl_version = 3, 3
    title = ""
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # monkey patch some things in
        wnd = kwargs.get('wnd')
        wnd.ctx.enable(mgl.BLEND)
        wnd.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        width, height = wnd.size
        wnd.vp = glm.ortho(-0.5/(height/width), 0.5/(height/width), -0.5, 0.5)
        wnd.clear_color = 0.3, 0.3, 0.3
        wnd.flip = flip.__get__(wnd)
        wnd.t0 = default_timer()


class ImWin(BaseWin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        wnd = kwargs.get('wnd')
        wnd.imgui = MglRenderer(wnd)
        self.imgui = wnd.imgui

    def resize(self, width: int, height: int):
        self.imgui.resize(width, height)

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)


Win = ImWin if has_imgui else BaseWin


def run_window_config(config_cls: WindowConfig, timer=None, args=None) -> None:
    """
    Adapted from moderngl_window's run_window_config
    Essentially the same thing, but we restrict a few things (e.g. always fullscreen, no cursor, ...)

    Also pre-calc the view-projection part of the matrix

    Run an WindowConfig entering a blocking main loop
    Args:
        config_cls: The WindowConfig class to render
        args: Override sys.args
    """
    # mglw.setup_basic_logging(config_cls.log_level)
    values = mglw.parse_args(args)
    window_cls = mglw.get_local_window_cls(values.window)

    # Calculate window size
    size = values.size or config_cls.window_size
    size = int(size[0] * values.size_mult), int(size[1] * values.size_mult)

    window = window_cls(
        title=config_cls.title,
        size=size,
        fullscreen=True,
        resizable=False,
        gl_version=config_cls.gl_version,
        aspect_ratio=config_cls.aspect_ratio,
        vsync=values.vsync,
        samples=values.samples if values.samples is not None else config_cls.samples,
        cursor=False,
    )
    window.print_context_info()
    mglw.activate_context(window=window)
    window.config = config_cls(ctx=window.ctx, wnd=window, timer=timer)
    window.clear(*window.clear_color)
    return window


if __name__ == '__main__':
    window = run_window_config(Win)

    # separate out event loop
    while not window.is_closing:
        window.clear()
        window.swap_buffers()

    window.destroy()
