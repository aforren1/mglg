#version 330

uniform vec2 accel;
uniform float dt;

in vec4 in_pos_alpha;
in vec4 in_prev_pos_alpha;
out vec4 out_pos_alpha;
out vec4 out_prev_pos_alpha;

void main()
{
    out_pos_alpha.xy = in_pos_alpha.xy * 2.0 - in_prev_pos_alpha.xy + accel;
    out_pos_alpha.z = 0; // fix this axis
    out_pos_alpha.w -= dt; // fade out particle
    out_prev_pos_alpha = in_pos_alpha;
}
