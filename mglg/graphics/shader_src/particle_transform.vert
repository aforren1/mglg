#version 330

//uniform vec2 accel;

in vec4 in_pos_alpha;
in vec4 in_prev_pos_alpha;
in vec4 accel;
out vec4 out_pos_alpha;
out vec4 out_prev_pos_alpha;

float rand(vec2 co)
{
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// how much to fade particle per timestep
float rescale(float x)
{
    // scale from [0, 1] to [0.001, 0.05]
    return (0.05 - 0.01) * x + 0.01;
}

void main()
{
    out_pos_alpha.xy = in_pos_alpha.xy * 2.0 - in_prev_pos_alpha.xy + accel.xy;
    out_pos_alpha.z = 0; // fix this axis
    out_pos_alpha.w = in_pos_alpha.w - rescale(rand(in_pos_alpha.xy)); // fade out particle
    out_prev_pos_alpha = in_pos_alpha;
}
