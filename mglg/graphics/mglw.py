import logging
import moderngl as mgl
from moderngl_window.context.base import WindowConfig
import moderngl_window as mglw
import glm
#import imgui
# from moderngl_window.integrations.imgui import ModernglWindowRenderer

# logger = logging.getLogger(__name__)

class Win(mglw.WindowConfig):
    gl_version = 3, 3
    title = ""
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #imgui.create_context()
        #self.imgui = ModernglWindowRenderer

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
    width, height = size
    ortho = glm.ortho(-0.5/(height/width), 0.5/(height/width), -0.5, 0.5)
    window.vp = ortho
    mglw.activate_context(window=window)
    window.config = config_cls(ctx=window.ctx, wnd=window, timer=timer)
    window.ctx.enable(mgl.BLEND)
    window.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
    return window


if __name__ == '__main__':
    window = run_window_config(Win)

    # separate out event loop
    while not window.is_closing:
        window.clear()
        window.swap_buffers()

    window.destroy()