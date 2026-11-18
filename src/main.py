import os
import csv
import time
import zlib
import struct
import ctypes
import glfw
import moderngl
import numpy as np
from pyrr import matrix44, Vector3


def get_process_memory_mb():
    """Retorna o consumo de memória RAM do processo em MB (compatível com Windows/Linux)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        if os.name == 'nt':
            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ('cb', ctypes.c_ulong),
                    ('PageFaultCount', ctypes.c_ulong),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t),
                ]
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return counters.WorkingSetSize / (1024 * 1024)
        return 0.0


def save_png(filepath, width, height, rgb_bytes):
    """Salva framebuffer RGB em PNG sem dependências externas."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # Inverte eixo Y (OpenGL tem origem no canto inferior esquerdo)
    row_stride = width * 3
    rows = [
        b'\x00' + rgb_bytes[y * row_stride:(y + 1) * row_stride]
        for y in range(height - 1, -1, -1)
    ]
    raw_data = b''.join(rows)

    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('!I', len(data)) + chunk + struct.pack('!I', zlib.crc32(chunk) & 0xffffffff)

    ihdr = struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(b'IHDR', ihdr)
        + png_chunk(b'IDAT', zlib.compress(raw_data, level=6))
        + png_chunk(b'IEND', b'')
    )
    with open(filepath, 'wb') as f:
        f.write(png_data)


def generate_complex_space_module():
    """
    Gera um módulo espacial detalhado com suporte a materiais e corredores de acoplamento:
    - Material 0.0 = Fuselagem Metálica (Branco/Prata)
    - Material 1.0 = Painéis Solares (Azul-Escuro Espelhado)
    Total: 420 triângulos por módulo (972 módulos = 408.240 triângulos).
    """
    verts, normals, mat_ids = [], [], []

    def add_quad(p1, p2, p3, p4, norm, mat_id):
        verts.extend([p1, p2, p3, p1, p3, p4])
        normals.extend([norm] * 6)
        mat_ids.extend([[mat_id]] * 6)

    def add_cylinder(r, length, axis='y', mat_id=0.0, segments=68):
        for i in range(segments):
            theta1 = (i / segments) * 2 * np.pi
            theta2 = ((i + 1) / segments) * 2 * np.pi
            c1, s1 = np.cos(theta1), np.sin(theta1)
            c2, s2 = np.cos(theta2), np.sin(theta2)

            if axis == 'y':
                p1, p2 = [r * c1, -length / 2, r * s1], [r * c2, -length / 2, r * s2]
                p3, p4 = [r * c2, length / 2, r * s2], [r * c1, length / 2, r * s1]
                n1, n2 = [c1, 0.0, s1], [c2, 0.0, s2]
            elif axis == 'x':
                p1, p2 = [-length / 2, r * c1, r * s1], [-length / 2, r * c2, r * s2]
                p3, p4 = [length / 2, r * c2, r * s2], [length / 2, r * c1, r * s1]
                n1, n2 = [0.0, c1, s1], [0.0, c2, s2]
            elif axis == 'z':
                p1, p2 = [r * c1, r * s1, -length / 2], [r * c2, r * s2, -length / 2]
                p3, p4 = [r * c2, r * s2, length / 2], [r * c1, r * s1, length / 2]
                n1, n2 = [c1, s1, 0.0], [c2, s1, 0.0]

            verts.extend([p1, p2, p3, p1, p3, p4])
            normals.extend([n1, n2, n2, n1, n2, n1])
            mat_ids.extend([[mat_id]] * 6)

    # 1. Módulo Central Vertical (Metal - Material 0.0) -> 68 * 2 = 136 triângulos
    add_cylinder(r=0.5, length=1.6, axis='y', mat_id=0.0, segments=68)

    # 2. Corredores de Acoplamento Horizontal (Eixos X e Z) -> 2 * 136 = 272 triângulos
    add_cylinder(r=0.25, length=4.0, axis='x', mat_id=0.0, segments=68)
    add_cylinder(r=0.25, length=4.0, axis='z', mat_id=0.0, segments=68)

    # 3. Tampas estruturais superior e inferior -> 4 triângulos
    r_cap = 0.5
    add_quad([-r_cap, 0.8, -r_cap], [r_cap, 0.8, -r_cap], [r_cap, 0.8, r_cap], [-r_cap, 0.8, r_cap], [0, 1, 0], 0.0)
    add_quad([-r_cap, -0.8, r_cap], [r_cap, -0.8, r_cap], [r_cap, -0.8, -r_cap], [-r_cap, -0.8, -r_cap], [0, -1, 0], 0.0)

    # 4. Painéis Solares (Silício/Vidro Azul - Material 1.0) -> 8 triângulos (Total = 420 triângulos)
    pw, ph = 1.8, 0.35
    add_quad([-pw, -ph / 2, 0], [-r_cap, -ph / 2, 0], [-r_cap, ph / 2, 0], [-pw, ph / 2, 0], [0, 0, 1], 1.0)
    add_quad([-pw, ph / 2, 0], [-r_cap, ph / 2, 0], [-r_cap, -ph / 2, 0], [-pw, -ph / 2, 0], [0, 0, -1], 1.0)
    add_quad([r_cap, -ph / 2, 0], [pw, -ph / 2, 0], [pw, ph / 2, 0], [r_cap, ph / 2, 0], [0, 0, 1], 1.0)
    add_quad([r_cap, ph / 2, 0], [pw, ph / 2, 0], [pw, -ph / 2, 0], [r_cap, -ph / 2, 0], [0, 0, -1], 1.0)

    v_arr = np.array(verts, dtype='f4')
    n_arr = np.array(normals, dtype='f4')
    m_arr = np.array(mat_ids, dtype='f4')

    return np.hstack([v_arr, n_arr, m_arr])


def generate_earth_sphere(radius=160.0, rings=64, sectors=64):
    """Gera uma esfera tridimensional de alta resolução para o Planeta Terra."""
    verts, normals, uvs = [], [], []
    for r in range(rings + 1):
        lat = np.pi * (-0.5 + r / rings)
        z0, r0 = np.sin(lat), np.cos(lat)
        for s in range(sectors + 1):
            lon = 2 * np.pi * (s / sectors)
            x0, y0 = np.cos(lon), np.sin(lon)
            x, y, z = x0 * r0, y0 * r0, z0

            verts.append([x * radius, y * radius, z * radius])
            normals.append([x, y, z])
            uvs.append([s / sectors, r / rings])

    indices = []
    for r in range(rings):
        for s in range(sectors):
            i1 = r * (sectors + 1) + s
            i2 = i1 + sectors + 1
            indices.extend([i1, i2, i1 + 1, i1 + 1, i2, i2 + 1])

    v_arr = np.array(verts, dtype='f4')[indices]
    n_arr = np.array(normals, dtype='f4')[indices]
    uv_arr = np.array(uvs, dtype='f4')[indices]

    return np.hstack([v_arr, n_arr, uv_arr])


def create_module_vao(ctx, program):
    mesh_data = generate_complex_space_module()
    vbo = ctx.buffer(mesh_data.tobytes())
    vao = ctx.vertex_array(program, [(vbo, '3f 3f 1f', 'in_position', 'in_normal', 'in_material')])
    num_vertices = len(mesh_data)
    return vao, num_vertices, vbo.size


def create_earth_vao(ctx, program):
    earth_data = generate_earth_sphere()
    vbo = ctx.buffer(earth_data.tobytes())
    vao = ctx.vertex_array(program, [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')])
    return vao, vbo.size


def create_starfield_vao(ctx, program, num_stars=3500):
    np.random.seed(42)
    positions = np.random.uniform(-500, 500, (num_stars, 3)).astype('f4')
    vbo = ctx.buffer(positions.tobytes())
    vao = ctx.vertex_array(program, [(vbo, '3f', 'in_position')])
    return vao, vbo.size


def extract_frustum_planes(view_proj_matrix):
    m = view_proj_matrix.T
    planes = [
        m[3] + m[0],  # Left
        m[3] - m[0],  # Right
        m[3] + m[1],  # Bottom
        m[3] - m[1],  # Top
        m[3] + m[2],  # Near
        m[3] - m[2]   # Far
    ]
    for i in range(6):
        length = np.linalg.norm(planes[i][:3])
        planes[i] = planes[i] / length
    return planes


def is_aabb_in_frustum(aabb_min, aabb_max, planes):
    for p in planes:
        px = aabb_max.x if p[0] > 0 else aabb_min.x
        py = aabb_max.y if p[1] > 0 else aabb_min.y
        pz = aabb_max.z if p[2] > 0 else aabb_min.z

        if p[0] * px + p[1] * py + p[2] * pz + p[3] < 0:
            return False
    return True


# Presets de Câmera para Testes Reprodutíveis
CAMERA_PRESETS = {
    "Cenario_1_Frontal_Completa": {
        "pos": Vector3([-1.0, 32.0, 92.0], dtype='f4'),
        "yaw": -90.0,
        "pitch": -20.0,
        "desc": "Visão Frontal Completa (100% da estação no frustum)"
    },
    "Cenario_2_Angulada_Parcial": {
        "pos": Vector3([18.0, 8.0, 24.0], dtype='f4'),
        "yaw": -128.0,
        "pitch": -12.0,
        "desc": "Visão Angulada Parcial (~30% a 40% da estação visível)"
    },
    "Cenario_3_Interna_Aproximada": {
        "pos": Vector3([-22.0, 2.0, -18.0], dtype='f4'),
        "yaw": -42.0,
        "pitch": -5.0,
        "desc": "Inspeção Interna Aproximada (~10% a 15% visível)"
    },
    "Cenario_4_Terra_Espaco_Vazio": {
        "pos": Vector3([0.0, -18.0, 65.0], dtype='f4'),
        "yaw": -90.0,
        "pitch": -42.0,
        "desc": "Órbita / Planeta Terra (0% dos módulos visíveis)"
    }
}

cam_pos = CAMERA_PRESETS["Cenario_1_Frontal_Completa"]["pos"].copy()
cam_yaw = CAMERA_PRESETS["Cenario_1_Frontal_Completa"]["yaw"]
cam_pitch = CAMERA_PRESETS["Cenario_1_Frontal_Completa"]["pitch"]
first_mouse = True
last_x, last_y = 640.0, 360.0


def mouse_callback(window, xpos, ypos):
    global cam_yaw, cam_pitch, first_mouse, last_x, last_y
    if first_mouse:
        last_x, last_y = xpos, ypos
        first_mouse = False

    dx = xpos - last_x
    dy = last_y - ypos
    last_x, last_y = xpos, ypos

    sensitivity = 0.15
    cam_yaw += dx * sensitivity
    cam_pitch += dy * sensitivity
    cam_pitch = max(-89.0, min(89.0, cam_pitch))


def apply_preset(preset_key):
    global cam_pos, cam_yaw, cam_pitch
    preset = CAMERA_PRESETS[preset_key]
    cam_pos = preset["pos"].copy()
    cam_yaw = preset["yaw"]
    cam_pitch = preset["pitch"]


def main():
    global cam_pos, cam_yaw, cam_pitch

    if not glfw.init():
        raise Exception("Erro ao inicializar GLFW")

    WIDTH, HEIGHT = 1280, 720
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WIDTH, HEIGHT, "Simulação Orbital - View Frustum Culling (RTX 4060 Benchmark)", None, None)
    if not window:
        glfw.terminate()
        raise Exception("Erro ao criar janela GLFW")

    glfw.make_context_current(window)
    # Desativa V-Sync por padrão para medições reais de FPS (alterne com tecla V)
    vsync_enabled = False
    glfw.swap_interval(0)

    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    ctx = moderngl.create_context()
    ctx.enable(moderngl.DEPTH_TEST)

    gpu_renderer = ctx.info.get('GL_RENDERER', 'GPU Desconhecida')
    print(f"-> Contexto OpenGL 3.3 Core inicializado em: {gpu_renderer}")

    # 1. Shader dos Módulos Espaciais (Iluminação Blinn-Phong + Materiais)
    module_prog = ctx.program(
        vertex_shader='''
            #version 330
            uniform mat4 m_proj;
            uniform mat4 m_view;
            uniform mat4 m_model;
            in vec3 in_position;
            in vec3 in_normal;
            in float in_material;
            out vec3 v_normal;
            out vec3 v_world_pos;
            out float v_material;
            void main() {
                vec4 world_pos = m_model * vec4(in_position, 1.0);
                v_world_pos = world_pos.xyz;
                gl_Position = m_proj * m_view * world_pos;
                v_normal = mat3(m_model) * in_normal;
                v_material = in_material;
            }
        ''',
        fragment_shader='''
            #version 330
            in vec3 v_normal;
            in vec3 v_world_pos;
            in float v_material;
            out vec4 f_color;

            void main() {
                vec3 N = normalize(v_normal);
                vec3 sun_dir = normalize(vec3(2.0, 4.0, 3.0));
                float diff = max(dot(N, sun_dir), 0.10);

                vec3 base_color;
                float shininess;

                if (v_material > 0.5) {
                    base_color = vec3(0.05, 0.20, 0.48);
                    shininess = 64.0;
                } else {
                    base_color = vec3(0.85, 0.88, 0.92);
                    shininess = 16.0;
                }

                vec3 view_dir = normalize(-v_world_pos);
                vec3 half_dir = normalize(sun_dir + view_dir);
                float spec = pow(max(dot(N, half_dir), 0.0), shininess);
                vec3 specular = vec3(0.75) * spec;

                f_color = vec4(base_color * diff + specular, 1.0);
            }
        '''
    )

    # 2. Shader Procedural do Planeta Terra
    earth_prog = ctx.program(
        vertex_shader='''
            #version 330
            uniform mat4 m_proj;
            uniform mat4 m_view;
            uniform mat4 m_model;
            in vec3 in_position;
            in vec3 in_normal;
            in vec2 in_uv;
            out vec3 v_normal;
            out vec2 v_uv;
            out vec3 v_world_pos;
            void main() {
                vec4 world_pos = m_model * vec4(in_position, 1.0);
                v_world_pos = world_pos.xyz;
                gl_Position = m_proj * m_view * world_pos;
                v_normal = mat3(m_model) * in_normal;
                v_uv = in_uv;
            }
        ''',
        fragment_shader='''
            #version 330
            in vec3 v_normal;
            in vec2 v_uv;
            in vec3 v_world_pos;
            out vec4 f_color;

            float hash(vec2 p) {
                return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
            }

            float noise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                float a = hash(i);
                float b = hash(i + vec2(1.0, 0.0));
                float c = hash(i + vec2(0.0, 1.0));
                float d = hash(i + vec2(1.0, 1.0));
                return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
            }

            void main() {
                vec3 N = normalize(v_normal);
                vec3 sun_dir = normalize(vec3(2.0, 4.0, 3.0));
                float diff = max(dot(N, sun_dir), 0.06);

                float n = noise(v_uv * 12.0) * 0.6 + noise(v_uv * 24.0) * 0.4;
                vec3 ocean = vec3(0.02, 0.14, 0.45);
                vec3 land = vec3(0.12, 0.40, 0.16);

                float land_mask = smoothstep(0.45, 0.52, n);
                vec3 surface = mix(ocean, land, land_mask);

                float cloud_noise = noise(v_uv * 30.0 + vec2(0.2, 0.5));
                float clouds = smoothstep(0.55, 0.70, cloud_noise);
                surface = mix(surface, vec3(0.96), clouds * 0.85);

                vec3 view_dir = normalize(-v_world_pos);
                float rim = 1.0 - max(dot(view_dir, N), 0.0);
                vec3 atmosphere = vec3(0.22, 0.55, 1.0) * pow(rim, 3.0);

                f_color = vec4(surface * diff + atmosphere * (diff + 0.25), 1.0);
            }
        '''
    )

    # 3. Shader das Estrelas
    star_prog = ctx.program(
        vertex_shader='''
            #version 330
            uniform mat4 m_proj;
            uniform mat4 m_view;
            in vec3 in_position;
            void main() {
                gl_Position = m_proj * m_view * vec4(in_position, 1.0);
            }
        ''',
        fragment_shader='''
            #version 330
            out vec4 f_color;
            void main() {
                f_color = vec4(1.0, 1.0, 1.0, 1.0);
            }
        '''
    )

    module_vao, verts_per_module, mod_vram = create_module_vao(ctx, module_prog)
    earth_vao, earth_vram = create_earth_vao(ctx, earth_prog)
    star_vao, star_vram = create_starfield_vao(ctx, star_prog)

    total_vram_kb = (mod_vram + earth_vram + star_vram) / 1024.0

    # Gerar Estação Espacial Modular em Grelha 3D Densa (972 Módulos Conectados)
    modules = []
    grid_size = 35
    for x in range(-grid_size, grid_size, 4):
        for y in range(-4, 5, 4):
            for z in range(-grid_size, grid_size, 4):
                pos = Vector3([x, y, z], dtype='f4')
                aabb_min = pos - Vector3([2.5, 1.0, 2.5], dtype='f4')
                aabb_max = pos + Vector3([2.5, 1.0, 2.5], dtype='f4')
                modules.append({
                    'matrix': matrix44.create_from_translation(pos, dtype='f4'),
                    'aabb_min': aabb_min,
                    'aabb_max': aabb_max
                })

    polys_per_module = verts_per_module // 3
    total_scene_polys = len(modules) * polys_per_module
    print(f"-> Estação Espacial gerada: {len(modules)} módulos ({polys_per_module} triângulos/módulo).")
    print(f"-> Complexidade da estação: {total_scene_polys:,} triângulos | VRAM Buffers: {total_vram_kb:.2f} KB.")
    print("-> Atalhos: [1-4] Presets Câmera | [C] Culling | [V] V-Sync | [B] Benchmark CSV | [F12] Screenshot")

    culling_enabled = True
    key_locks = {}

    def key_just_pressed(key):
        is_down = glfw.get_key(window, key) == glfw.PRESS
        was_down = key_locks.get(key, False)
        key_locks[key] = is_down
        return is_down and not was_down

    # Estado do Benchmark Automatizado
    benchmark_active = False
    benchmark_queue = []
    benchmark_results = []
    bench_stage_start = 0.0
    bench_frames = 0
    bench_frame_times = []

    last_time = time.time()
    frames = 0
    dt_last = time.time()

    earth_pos = Vector3([0.0, -210.0, 0.0], dtype='f4')
    earth_matrix = matrix44.create_from_translation(earth_pos, dtype='f4')

    while not glfw.window_should_close(window):
        t_now = time.time()
        dt = t_now - dt_last
        dt_last = t_now

        glfw.poll_events()

        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        if not benchmark_active:
            if key_just_pressed(glfw.KEY_C):
                culling_enabled = not culling_enabled
                print(f"-> View Frustum Culling: {'LIGADO' if culling_enabled else 'DESLIGADO'}")

            if key_just_pressed(glfw.KEY_V):
                vsync_enabled = not vsync_enabled
                glfw.swap_interval(1 if vsync_enabled else 0)
                print(f"-> V-Sync: {'LIGADO' if vsync_enabled else 'DESLIGADO'}")

            if key_just_pressed(glfw.KEY_1):
                apply_preset("Cenario_1_Frontal_Completa")
                print("-> Câmera: Cenário 1 (Visão Frontal Completa)")
            elif key_just_pressed(glfw.KEY_2):
                apply_preset("Cenario_2_Angulada_Parcial")
                print("-> Câmera: Cenário 2 (Visão Angulada Parcial)")
            elif key_just_pressed(glfw.KEY_3):
                apply_preset("Cenario_3_Interna_Aproximada")
                print("-> Câmera: Cenário 3 (Inspeção Interna Aproximada)")
            elif key_just_pressed(glfw.KEY_4):
                apply_preset("Cenario_4_Terra_Espaco_Vazio")
                print("-> Câmera: Cenário 4 (Planeta Terra / Espaço Vazio)")

            if key_just_pressed(glfw.KEY_B):
                print("\n========================================================")
                print(" INICIANDO BATERIA DE BENCHMARK AUTOMATIZADO (8 TESTES)")
                print("========================================================")
                glfw.swap_interval(0)
                vsync_enabled = False
                benchmark_active = True
                benchmark_results = []
                benchmark_queue = []
                for preset_name in CAMERA_PRESETS.keys():
                    benchmark_queue.append((preset_name, False))
                    benchmark_queue.append((preset_name, True))
                cur_preset, cur_cull = benchmark_queue[0]
                apply_preset(cur_preset)
                culling_enabled = cur_cull
                bench_stage_start = time.time()
                bench_frames = 0
                bench_frame_times = []

        # Direção da Câmara
        rad_yaw = np.radians(cam_yaw)
        rad_pitch = np.radians(cam_pitch)

        front = Vector3([
            np.cos(rad_yaw) * np.cos(rad_pitch),
            np.sin(rad_pitch),
            np.sin(rad_yaw) * np.cos(rad_pitch)
        ], dtype='f4')
        cam_front = Vector3(front / np.linalg.norm(front), dtype='f4')

        right = Vector3(np.cross(cam_front, [0.0, 1.0, 0.0]), dtype='f4')
        cam_right = Vector3(right / np.linalg.norm(right), dtype='f4')

        # Movimento manual (desabilitado durante benchmark)
        if not benchmark_active:
            speed = 35.0 * dt
            if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
                cam_pos += cam_front * speed
            if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
                cam_pos -= cam_front * speed
            if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
                cam_pos += cam_right * speed
            if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
                cam_pos -= cam_right * speed
            if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
                cam_pos.y += speed
            if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
                cam_pos.y -= speed

        proj = matrix44.create_perspective_projection_matrix(60.0, WIDTH / HEIGHT, 0.1, 1000.0, dtype='f4')
        view = matrix44.create_look_at(cam_pos, cam_pos + cam_front, [0.0, 1.0, 0.0], dtype='f4')

        module_prog['m_proj'].write(proj)
        module_prog['m_view'].write(view)

        earth_prog['m_proj'].write(proj)
        earth_prog['m_view'].write(view)
        earth_prog['m_model'].write(earth_matrix)

        star_prog['m_proj'].write(proj)
        star_prog['m_view'].write(view)

        view_proj = matrix44.multiply(view, proj)
        planes = extract_frustum_planes(view_proj)

        ctx.clear(0.01, 0.01, 0.03)

        # 1. Desenhar Estrelas
        star_vao.render(mode=moderngl.POINTS)

        # 2. Desenhar a Terra
        earth_vao.render()

        # 3. Desenhar Módulos com View Frustum Culling
        rendered_count = 0
        for mod in modules:
            if culling_enabled:
                if not is_aabb_in_frustum(mod['aabb_min'], mod['aabb_max'], planes):
                    continue

            module_prog['m_model'].write(mod['matrix'])
            module_vao.render()
            rendered_count += 1

        glfw.swap_buffers(window)

        # Captura de Screenshot com F12
        if key_just_pressed(glfw.KEY_F12):
            fb_width, fb_height = glfw.get_framebuffer_size(window)
            pixels = ctx.fbo.read(components=3)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cull_tag = "culling_ON" if culling_enabled else "culling_OFF"
            filename = f"docs/screenshots/captura_{cull_tag}_{timestamp}.png"
            save_png(filename, fb_width, fb_height, pixels)
            print(f"-> [SCREENSHOT] Salva em: {filename}")

        # Processamento do Benchmark Automatizado (2.5s por cenário: 0.5s warmup + 2.0s medição)
        if benchmark_active:
            elapsed_stage = time.time() - bench_stage_start
            if elapsed_stage > 0.5:
                bench_frames += 1
                if dt > 0:
                    bench_frame_times.append(dt * 1000.0)

            if elapsed_stage >= 2.5:
                cur_preset, cur_cull = benchmark_queue.pop(0)
                measure_duration = elapsed_stage - 0.5
                avg_fps = bench_frames / measure_duration if measure_duration > 0 else 0.0
                avg_ms = np.mean(bench_frame_times) if bench_frame_times else 0.0
                ram_mb = get_process_memory_mb()
                discarded_modules = len(modules) - rendered_count
                discard_pct = (discarded_modules / len(modules)) * 100.0
                rendered_polys = rendered_count * polys_per_module

                benchmark_results.append({
                    "cenario": cur_preset,
                    "culling": "LIGADO" if cur_cull else "DESLIGADO",
                    "fps": round(avg_fps, 1),
                    "frame_time_ms": round(avg_ms, 3),
                    "modulos_renderizados": rendered_count,
                    "total_modulos": len(modules),
                    "triangulos_gpu": rendered_polys,
                    "descarte_pct": round(discard_pct, 1),
                    "ram_mb": round(ram_mb, 1),
                    "vram_buffers_kb": round(total_vram_kb, 2)
                })

                # Captura automática de screenshot para os cenários 1 e 4 com Culling LIGADO
                if cur_cull and cur_preset in ("Cenario_1_Frontal_Completa", "Cenario_4_Terra_Espaco_Vazio"):
                    fb_w, fb_h = glfw.get_framebuffer_size(window)
                    save_png(f"docs/screenshots/{cur_preset}.png", fb_w, fb_h, ctx.fbo.read(components=3))

                if benchmark_queue:
                    next_preset, next_cull = benchmark_queue[0]
                    apply_preset(next_preset)
                    culling_enabled = next_cull
                    bench_stage_start = time.time()
                    bench_frames = 0
                    bench_frame_times = []
                else:
                    benchmark_active = False
                    os.makedirs("results", exist_ok=True)
                    csv_path = "results/benchmark_metrics.csv"
                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=benchmark_results[0].keys())
                        writer.writeheader()
                        writer.writerows(benchmark_results)

                    print("\n-> BENCHMARK CONCLUÍDO! Resultados salvos em:", csv_path)
                    for r in benchmark_results:
                        print(
                            f"   {r['cenario']:30s} | {r['culling']:9s} | "
                            f"{r['fps']:7.1f} FPS | {r['frame_time_ms']:6.3f} ms | "
                            f"Descarte: {r['descarte_pct']:5.1f}% | RAM: {r['ram_mb']} MB"
                        )
                    print("========================================================\n")

        frames += 1
        if t_now - last_time >= 1.0 and not benchmark_active:
            rendered_polys = rendered_count * polys_per_module
            ms_per_frame = 1000.0 / frames if frames > 0 else 0.0
            discard_pct = ((len(modules) - rendered_count) / len(modules)) * 100.0
            ram_mb = get_process_memory_mb()
            print(
                f"Culling: {'LIGADO' if culling_enabled else 'DESLIGADO':9s} | "
                f"FPS: {frames:4d} ({ms_per_frame:5.2f} ms) | "
                f"Objetos: {rendered_count:3d}/{len(modules)} (-{discard_pct:4.1f}%) | "
                f"Polígonos: {rendered_polys:7,d} | RAM: {ram_mb:5.1f} MB"
            )
            frames = 0
            last_time = t_now

    glfw.terminate()


if __name__ == '__main__':
    main()