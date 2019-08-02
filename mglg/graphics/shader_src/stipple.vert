#version 330
uniform mat4 mvp;

in vec3 vertices;
in float dist;

out float out_dist;
void main()
{
    out_dist = dist;
    gl_Position = mvp * vec4(vertices, 1.0);
}
