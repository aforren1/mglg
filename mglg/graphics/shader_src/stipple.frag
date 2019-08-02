#version 330
uniform vec4 color;
uniform vec2 u_resolution;
uniform float u_dash_size;
uniform float u_gap_size;

in float out_dist;
out vec4 f_color;

void main()
{
    float dash_gap = u_dash_size + u_gap_size;
    if (fract(out_dist / dash_gap) > u_dash_size / dash_gap)
        discard;
    f_color = color;
}
