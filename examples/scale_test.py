
if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.graphics.shapes import Rect, Circle, Arrow, Polygon, Cross
    from mglg.graphics.image import Image
    from mglg.graphics.particles import Particles
    from mglg.graphics.text import Text
    from glm import vec4
    import os.path as op

    win = Win(vsync=1, screen=0)

    scales = [0.025, 0.05, 0.1, [0.1, 0.15], 0.2, [0.3, 0.1]]
    offsets = [0.4, 0.2, 0, -0.2, 0.2, -0.4] # distance between rows

    check_path = op.join(op.dirname(__file__), 'check_small.png')
    check = Image(win, check_path)
    
    sqr = Rect(win, fill_color=(0.7, 0.9, 0.2, 1), is_outlined=False)
    heit = Rect(win, fill_color=0.5, position=(-0.7, 0), scale=(0.05, 0.995))
    cir = Circle(win, fill_color=(0.9, 0.5, 0.2, 0.5), 
                 outline_color=(0.1, 0.9, 0.9, 0.5), outline_thickness=0.1)
    poly = Polygon(win, segments=7, fill_color=(0.9, 0.2, 0.2, 0.5), 
                   outline_color=(0.1, 0.1, 0.1, 1), outline_thickness=0.25)

    prt = Particles(win, num_particles=5e4, initial_scale_range=(0.2, 0.2),
                     final_scale_range=(0.2, 0.3), initial_alpha_range=(1,1),
                     final_alpha_range=(1,1))
    font_path = op.join(op.dirname(__file__), '../fonts/UbuntuMono-B.pklfont')
    txt = Text(win, 'A', font=font_path)

    # approx gamma correction
    x = Rect(win, position=(0.7, 0), outline_color=(0, 1, 1, 1), scale=0.1)

    tmp = 1/2.2
    noncorr = [vec4(0, 0, 0, 1), vec4(0.25, 0.25, 0.25, 1), vec4(0.5, 0.5, 0.5, 1),
               vec4(0.75, 0.75, 0.75, 1), vec4(1, 1, 1, 1)]
    corr = [r**tmp for r in noncorr]
    while not win.should_close:
        heit.draw()
        prt.spawn(10)
        for o, obj in zip(offsets, [check, sqr, prt, txt, cir, poly]):
            obj.position.y = o
            obj.position.x = -0.6
            for s in scales:
                obj.scale = s
                obj.draw()
                obj.position.x += 0.2
        x.position = 0.7, 0.4
        for nc, c in zip(noncorr, corr):
            x.fill_color = nc
            x.draw()
            x.position.x += 0.1
            x.fill_color = c
            x.draw()
            x.position.x -= 0.1
            x.position.y -= 0.2

        win.flip()
