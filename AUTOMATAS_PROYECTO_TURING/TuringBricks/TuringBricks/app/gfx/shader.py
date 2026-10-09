"""Sombreador de «plástico de juguete»: luz solar suave, luz de cielo,
brillo especular, borde iluminado y niebla atmosférica."""
from ursina import Shader, Vec3, color

plastic_shader = Shader(language=Shader.GLSL, name="plastic_shader", vertex='''
#version 150
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
in vec2 p3d_MultiTexCoord0;
uniform vec2 texture_scale;
out vec2 uv;
out vec3 w_pos;
out vec3 w_nrm;
out vec4 v_col;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    w_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;
    w_nrm = normalize(transpose(inverse(mat3(p3d_ModelMatrix))) * p3d_Normal);
    v_col = p3d_Color;
    uv = p3d_MultiTexCoord0 * texture_scale;
}''', fragment='''
#version 150
uniform vec4 p3d_ColorScale;
uniform vec3 cam_pos;
uniform vec3 sun_dir;
uniform vec3 fog_col;
uniform float fog_near;
uniform float fog_far;
uniform float glow;
uniform float spec_k;
uniform sampler2D p3d_Texture0;
in vec2 uv;
in vec3 w_pos;
in vec3 w_nrm;
in vec4 v_col;
out vec4 frag;
void main() {
    vec4 base = texture(p3d_Texture0, uv) * v_col * p3d_ColorScale;
    vec3 n = normalize(w_nrm);
    vec3 v = normalize(cam_pos - w_pos);
    vec3 l = normalize(-sun_dir);
    float diff = max(dot(n, l), 0.0);
    float sky = 0.5 + 0.5 * n.y;
    vec3 amb = mix(vec3(0.42, 0.40, 0.36), vec3(0.70, 0.78, 0.92), sky);
    vec3 h = normalize(l + v);
    float spec = pow(max(dot(n, h), 0.0), 48.0) * spec_k;
    float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.18;
    vec3 c = base.rgb * (amb * 0.72 + vec3(1.0, 0.96, 0.88) * diff * 0.62) + spec + rim;
    c = mix(c, base.rgb * 1.25 + 0.15, glow);
    float d = length(cam_pos - w_pos);
    float f = clamp((d - fog_near) / (fog_far - fog_near), 0.0, 1.0);
    c = mix(c, fog_col, f * f);
    frag = vec4(c, base.a);
}''', default_input={
    "cam_pos": Vec3(0, 10, -30), "sun_dir": Vec3(-0.45, -1.0, 0.55), "fog_col": Vec3(0.80, 0.90, 0.98),
    "fog_near": 70.0, "fog_far": 300.0, "glow": 0.0, "spec_k": 0.38, "texture_scale": (1, 1),
})
