
if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.graphics.shape2d import Square, Circle, Arrow, Polygon, Cross
    from mglg.graphics.image2d import Image2D
    from mglg.graphics.particle2d import Particle2D
    from mglg.graphics.text2d import Text2D
    import os.path as op

    win = Win(vsync=1, screen=0)

    scales = [0.025, 0.05, 0.1, [0.1, 0.15], 0.2, [0.3, 0.1]]
    offsets = [0.4, 0.2, 0, -0.2, 0.2, -0.4] # distance between rows

    check_path = op.join(op.dirname(__file__), 'check_small.png')
    check = Image2D(win, check_path)
    
    sqr = Square(win, fill_color=(0.7, 0.9, 0.2, 1), is_outlined=False)
    cir = Circle(win, fill_color=(0.9, 0.5, 0.2, 0.5), 
                 outline_color=(0.1, 0.9, 0.9, 0.5), outline_thickness=0.1)
    poly = Polygon(win, segments=7, fill_color=(0.9, 0.2, 0.2, 0.5), 
                   outline_color=(0.1, 0.1, 0.1, 1))

    prt = Particle2D(win, num_particles=5e4, initial_scale_range=(0.2, 0.2),
                     final_scale_range=(0.2, 0.3))
    font_path = op.join(op.dirname(__file__), 'UbuntuMono-B.ttf')
    txt = Text2D(win, 'X', font=font_path)

    while not win.should_close:
        prt.spawn(100)
        for o, obj in zip(offsets, [check, sqr, prt, txt, cir, poly]):
            obj.position.y = o
            obj.position.x = -0.6
            for s in scales:
                obj.scale = s
                obj.draw()
                obj.position.x += 0.2
        win.flip()
