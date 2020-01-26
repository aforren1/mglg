import numpy as np
import moderngl as mgl
from timeit import default_timer
from mglg.graphics.drawable import Drawable2D

# derived from https://github.com/moderngl/moderngl/blob/master/examples/particle_system_emit.py
vert_str = """
#version 330
uniform mat4 mvp;
in vec2 in_pos;
in vec4 in_color;
out vec4 color;
void main() {
    gl_Position = mvp * vec4(in_pos, 0.0, 1.0);
    //gl_PointSize = 3;
    color = in_color;
}
"""

frag_str = """
#version 330
in vec4 color;
out vec4 f_color;
void main() { f_color = color; }
"""

trans_vert_str = """
#version 330
in vec2 in_pos;
in vec2 in_vel;
in vec4 in_color;
out vec2 vs_vel;
out vec4 vs_color;
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    vs_vel = in_vel;
    vs_color = in_color;
}
"""

trans_geom_str = """
#version 330
layout(points) in;
layout(points, max_vertices = 1) out;

uniform float gravity = -0.2;
uniform float ft = 0.016; // frame time

in vec2 vs_vel[1];
in vec4 vs_color[1];

out vec2 out_pos;
out vec2 out_vel;
out vec4 out_color;

void main() {
    vec2 pos = gl_in[0].gl_Position.xy;
    vec4 color = vs_color[0];
    vec2 velocity = vs_vel[0];

    if (pos.y > -4 && color.a > 0) {
        vec2 vel = velocity + vec2(0.0, gravity);
        out_pos = pos + vel*ft;
        out_vel = vel;
        out_color = color;
        out_color.a -= ft*1.5; // TODO: tweak
        EmitVertex();
        EndPrimitive();
    }
}
"""

gpu_emitter_str = """
#version 330
#define M_PI 3.1415926535897932384626433832795

uniform vec2 mouse_pos = vec2(0.0, 0.0);
uniform vec2 mouse_vel = vec2(0.0, 0.0);
// removed mouse_vel
uniform float time;

out vec2 out_pos;
out vec2 out_vel;
out vec4 out_color;

float rand(float n){return fract(sin(n) * 43758.5453123);}

void main() {
    float a = mod(time * gl_VertexID, M_PI*2);
    float a2 = mod(time * gl_VertexID, M_PI*2);
    float r = rand(time + gl_VertexID)*6; // TODO
    float r2 = rand(time + gl_VertexID)*0.1;
    out_pos = mouse_pos + vec2(sin(a2), cos(a2)) * r2;
    out_vel = mouse_vel + vec2(sin(a), cos(a)) * r;
    out_color = vec4(clamp(rand(time * 3.4 + gl_VertexID), 0.9, 1.0), 
                     rand(time * 2.2 + gl_VertexID), 
                     rand(time * 1.1 + gl_VertexID)*0.1, 
                     clamp(rand(time * 3.5 + gl_VertexID), 0.2, 1.0));
}
"""


class ParticleBurst2D(Drawable2D):
    def __init__(self, win, num_particles=1e5, *args, **kwargs):
        super().__init__(win, *args, **kwargs)
        ctx = win.ctx
        ctx.point_size = 3.0
        # ctx.enable(mgl.PROGRAM_POINT_SIZE)
        self.t0 = default_timer()
        from glm import vec2
        self.prev_pos = vec2()

        self.prog = ctx.program(
            vertex_shader=vert_str,
            fragment_shader=frag_str
        )

        self.transform = ctx.program(
            vertex_shader=trans_vert_str,
            geometry_shader=trans_geom_str,
            varyings=['out_pos', 'out_vel', 'out_color']
        )

        self.N = int(num_particles)
        self.stride = 32  # byte stride per vertex
        self.max_emit_count = self.N // 20
        self.active_particles = 0  # start w/ nuthin
        self.vbo1 = ctx.buffer(reserve=self.N * self.stride, dynamic=True)
        self.vbo2 = ctx.buffer(reserve=self.N * self.stride, dynamic=True)

        self.transform_vao1 = ctx.vertex_array(
            self.transform,
            [(self.vbo1, '2f 2f 4f', 'in_pos', 'in_vel', 'in_color')]
        )
        self.transform_vao2 = ctx.vertex_array(
            self.transform,
            [(self.vbo2, '2f 2f 4f', 'in_pos', 'in_vel', 'in_color')]
        )
        self.render_vao1 = ctx.vertex_array(
            self.prog,
            [(self.vbo1, '2f 2x4 4f', 'in_pos', 'in_color')]
        )
        self.render_vao2 = ctx.vertex_array(
            self.prog,
            [(self.vbo2, '2f 2x4 4f', 'in_pos', 'in_color')]
        )

        self.gpu_emitter_prog = ctx.program(
            vertex_shader=gpu_emitter_str,
            varyings=['out_pos', 'out_vel', 'out_color']
        )
        # empty VAO (need moderngl>=5.6?)
        self.gpu_emitter_vao = ctx._vertex_array(self.gpu_emitter_prog, [])

        self.query = ctx.query(primitives=True)
        self.should_explode = False

    def explode(self):
        self.should_explode = True

    def draw(self):
        if self.visible:
            # gpu stuff here
            with self.query:
                self.transform_vao1.transform(self.vbo2, mgl.POINTS, vertices=self.active_particles)

            if self.should_explode:
                self.should_explode = False
                self._count = 3
            emit_count = 0
            if self._count > 0:
                self._count -= 1
                emit_count = self.N // 20
            #emit_count = min(self.N - self.query.primitives, self.max_emit_count)
            qp = self.query.primitives
            if emit_count > 0:
                self.gpu_emitter_prog['mouse_pos'].value = self.position[0], self.position[1]
                self.gpu_emitter_prog['mouse_vel'].write(memoryview((self.position - self.prev_pos)/0.016))
                self.gpu_emitter_prog['time'].value = default_timer() - self.t0
                self.gpu_emitter_vao.transform(self.vbo2, vertices=emit_count,
                                               buffer_offset=qp*self.stride)

            self.active_particles = qp + emit_count  # ??
            if self.active_particles > 0:
                mvp = self.win.vp * self.model_matrix
                self.prog['mvp'].write(memoryview(mvp))
                self.render_vao2.render(mgl.POINTS, vertices=self.active_particles)

            self.transform_vao1, self.transform_vao2 = self.transform_vao2, self.transform_vao1
            self.render_vao1, self.render_vao2 = self.render_vao2, self.render_vao1
            self.vbo1, self.vbo2 = self.vbo2, self.vbo1
            self.prev_pos = self.position[0], self.position[1]


if __name__ == '__main__':
    from mglg.graphics.win import Win
    from mglg.graphics.shape2d import Circle
    from math import sin, cos

    win = Win()

    counter = 0
    parts = ParticleBurst2D(win, num_particles=1e5)
    circ = Circle(win, is_filled=False, scale=0.1)
    parts.scale = 0.1

    for i in range(1000):
        if counter % 60 == 0:
            parts.explode()
        parts.position.xy = win.mouse_pos
        parts.draw()
        circ.draw()
        win.flip()
        if win.dt > 0.02:
            print(win.dt)
        if win.should_close:
            break
        counter += 1
