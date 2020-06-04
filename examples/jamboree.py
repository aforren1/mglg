import os.path as op
import imgui
from timeit import default_timer
import numpy as np
import moderngl as mgl
from math import sin, cos
from mglg.graphics import Win
import glm
from mglg.graphics import DrawableGroup

from mglg.graphics import Rect, Circle, Arrow, Polygon, Cross, RoundedRect, Shape
from mglg.graphics.shapes import make_rounded_rect
from mglg.graphics.image import Image, texture_cache
from mglg.graphics import Particles
from mglg.graphics.stipples import StippleArrow
from mglg.graphics import Text, DynamicText
from mglg.graphics import Framebuffer
from mglg.util.profiler import Profiler
# from toon.util import priority
# import gamemode as gm

if __name__ == '__main__':
    win = Win(vsync=1, screen=0, use_imgui=True)

    sqr = Rect(win, scale=(0.15, 0.1), fill_color=(0.7, 0.9, 0.2, 1), rotation=45)
    rr = RoundedRect(win, scale=(0.3, 0.1), fill_color=(0, 0.1, 0.7, 1), rotation=30,
                     position=(0.3, -0.2), radii=(1, 0.2, 1, 0.2), segments=32)
    # prescaling the vertices leads to the right outline scaling
    vs = make_rounded_rect(radii=(1, 0.2, 1, 0.2), segments=32)*(.3, .1)
    rr2 = Shape(win, vertices=vs, 
                fill_color=(0, 0.1, 0.7, 1), rotation=30,
                position=(0.5, -0.2), outline_color=(0.5, .9, 0, 1),
                outline_thickness=0.05*.15)
    circle = Circle(win, scale=(0.15, 0.1), fill_color=(0.2, 0.9, 0.7, 1))
    arrow = Arrow(win, scale=(0.15, 0.1), fill_color=(0.9, 0.7, 0.2, 1))
    circle.position.x += 0.2
    arrow.position.x -= 0.2
    sqr2 = Rect(win, scale=(0.05, 0.05), fill_color=(0.1, 0.1, 0.1, 0.6))
    poly = Polygon(win, segments=7, scale=(0.08, 0.08), position=(-0.2, -0.2),
                   fill_color=(0.9, 0.2, 0.2, 0.5), outline_color=(0.1, 0.1, 0.1, 1))
    crs = Cross(win, fill_color=(0.2, 0.1, 0.9, 0.7), is_outlined=False,
                scale=(0.12, 0.10), position=(0.3, 0.3))

    check_path = op.join(op.dirname(__file__), 'check_small.png')
    check = Image(win, check_path, position=(-0.2, 0.3),
                    scale=(0.1, 0.1), rotation=70)

    check2 = Image(win, check_path, position=(0.5, 0),
                     scale=(0.05, 0.05), rotation=0)
    fbo = Framebuffer(win, clear_color=(0, 0, 0.5), alpha=0.5,
              position=(0.4, 0), scale=(0.2, 0.3))
    # check that they *do* share the same vertex array
    assert sqr.vao == sqr2.vao

    particles = Particles(win, scale=0.4, num_particles=5e4)

    stiparrow = StippleArrow(win, scale=(0.1, 0.1),
                             position=(0.2, -0.3), pattern=0xadfa)

    # bump up font size for crisper look
    # font_path = op.join(op.dirname(__file__), 'UbuntuMono-B.ttf')
    font_path = op.join(op.dirname(__file__), '..', 'fonts', 'UbuntuMono-B.pklfont')
    bases = Text(win, scale=(0.1, 0.1), fill_color=(1, 0.1, 0.1, 0.7),
                   text='Tengo un gatito pequeñito', font=font_path, position=(0, -0.4))
    font_path = op.join(op.dirname(__file__), '..', 'fonts', 'AlexBrush-Regular.pklfont')
    bases2 = Text(win, scale=(0.15, 0.15), fill_color=(0.1, 1, 0.1, 1),
                    text='pequeño', font=font_path, position=(-0.4, 0), rotation=90)

    countup = DynamicText(win, text='0', scale=0.05, expected_chars=8,
                            font=font_path, position=(0.6, 0.4),
                            prefetch='0123456789')

    dg = DrawableGroup([sqr, sqr2, circle, arrow, poly, crs, rr, rr2])
    pix = DrawableGroup([check, check2])
    prt = DrawableGroup([particles])
    stp = DrawableGroup([stiparrow])
    txt = DrawableGroup([countup, bases, bases2])
    prof = Profiler(gpu=True, ctx=win.ctx)
    prof.active = True

    def update(win, counter):
        counter += 1
        sqr2.position = sin(counter/200)/2, cos(counter/200)/3
        sqr2.rotation = 2*counter
        sqr.rotation = -counter
        arrow.rotation = counter
        circle.rotation = counter
        stiparrow.rotation = -counter
        if counter % 11 == 0:
            countup.text = str(counter)
        countup.color = np.random.random(4)
        if counter % 100 == 0:
            particles.spawn(1000)
        dg.draw()
        pix.draw()
        prt.draw()
        stp.draw()
        txt.draw()
        with fbo:
            dg.draw(fbo.vp)
        fbo.draw()
        imgui.new_frame()
        imgui.show_demo_window()
        return counter

    counter = 0
    vals = []
    dts = []
    for i in range(int(60 * 60 * 2)):
        with prof:
            counter = update(win, counter)
        imgui.set_next_window_position(10, 10)
        imgui.set_next_window_size(270, 300)
        imgui.begin('stats (milliseconds)')
        imgui.text('Worst CPU: %f' % prof.worst_cpu)
        imgui.plot_lines('CPU', prof.cpubuffer,
                            scale_min=0, scale_max=30, graph_size=(180, 100))
        imgui.text('Worst GPU: %f' % prof.worst_gpu)
        imgui.plot_lines('GPU', prof.gpubuffer,
                            scale_min=0, scale_max=10, graph_size=(180, 100))
        imgui.end()
        win.flip()
        dts.append(win.dt)
        if win.should_close:
            break
    win.close()
    # import glfw
    # import matplotlib.pyplot as plt
    # glfw.terminate()
    # plt.plot(dts[3:])
    # vals = dts[3:]
    # plt.show()
