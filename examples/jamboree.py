import os.path as op
from timeit import default_timer
import numpy as np
import moderngl as mgl
from math import sin, cos
from mglg.graphics.win import Win
import glm
from mglg.graphics.drawable import DrawableGroup

from mglg.graphics.shape2d import Square, Circle, Arrow, Polygon, Cross
from mglg.graphics.image2d import Image2D, texture_cache
from mglg.graphics.particle2d import ParticleBurst2D
from mglg.graphics.stipple2d import StippleArrow
from mglg.graphics.text2d import Text2D, DynamicText2D
# from toon.util import priority
# import gamemode as gm

if __name__ == '__main__':
    win = Win(vsync=1, screen=0)
    win.ctx.line_width = 3.0

    sqr = Square(win, scale=(0.15, 0.1), fill_color=(0.7, 0.9, 0.2, 1), rotation=45)
    circle = Circle(win, scale=(0.15, 0.1), fill_color=(0.2, 0.9, 0.7, 1))
    arrow = Arrow(win, scale=(0.15, 0.1), fill_color=(0.9, 0.7, 0.2, 1))
    circle.position.x += 0.2
    arrow.position.x -= 0.2
    sqr2 = Square(win, scale=(0.05, 0.05), fill_color=(0.1, 0.1, 0.1, 0.6))
    poly = Polygon(win, segments=7, scale=(0.08, 0.08), position=(-0.2, -0.2),
                   fill_color=(0.9, 0.2, 0.2, 0.5), outline_color=(0.1, 0.1, 0.1, 1))
    crs = Cross(win, fill_color=(0.2, 0.1, 0.9, 0.7), is_outlined=False,
                scale=(0.12, 0.10), position=(0.3, 0.3))

    check_path = op.join(op.dirname(__file__), 'check_small.png')
    check = Image2D(win, check_path, position=(-0.2, 0.3),
                    scale=(0.1, 0.1), rotation=70)

    check2 = Image2D(win, check_path, position=(0.5, 0),
                     scale=(0.05, 0.05), rotation=0)
    # check that they *do* share the same vertex array
    assert sqr.vao_fill == sqr2.vao_fill

    particles = ParticleBurst2D(win, scale=0.1, num_particles=1e5)

    stiparrow = StippleArrow(win, scale=(0.1, 0.1),
                             position=(0.2, -0.3), pattern=0xadfa)

    # bump up font size for crisper look
    font_path = op.join(op.dirname(__file__), 'UbuntuMono-B.ttf')
    bases = Text2D(win, scale=(0.1, 0.1), color=(1, 0.1, 0.1, 0.7),
                   text='\u2620Tengo un gatito pequeñito\u2620', font=font_path, position=(0, -0.4))
    bases2 = Text2D(win, scale=(0.05, 0.05), color=(0.1, 1, 0.1, 1),
                    text='\u2611pequeño\u2611', font=font_path, position=(-0.4, 0), rotation=90)

    countup = DynamicText2D(win, text='0', scale=0.05, expected_chars=8,
                            font=font_path, position=(-0.6, 0.4),
                            prefetch='0123456789')

    dg = DrawableGroup([sqr, sqr2, circle, arrow, poly, crs])
    pix = DrawableGroup([check, check2])
    prt = DrawableGroup([particles])
    stp = DrawableGroup([stiparrow])
    txt = DrawableGroup([countup, bases, bases2])
    #qry = win.ctx.query(time=True)

    def update(win, counter):
        counter += 4
        sqr2.position = sin(counter/200)/2, cos(counter/200)/3
        sqr2.rotation = 2*counter
        sqr.rotation = -counter
        arrow.rotation = counter
        circle.rotation = counter
        stiparrow.rotation = -counter
        countup.text = str(counter)
        countup.color = np.random.random(4)
        #with qry:
        if counter % 100 == 0:
            particles.explode()
        dg.draw()
        pix.draw()
        prt.draw()
        stp.draw()
        txt.draw()
        #if counter % 10 == 0:
        #    print('GPU time: %f ms' % (qry.elapsed/1000000))
        return counter

    counter = 0
    vals = []
    dts = []
    for i in range(int(60 * 60 * 1)):
        t0 = default_timer()
        counter = update(win, counter)
        vals.append(default_timer() - t0)
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
    print('mean: %f, std: %f, max: %f' % (np.mean(vals), np.std(vals), max(vals)))
