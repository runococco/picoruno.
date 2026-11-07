# Renders the layers for donguri.html: an autumn forest clearing seen from the front with wooden chutes that split twice
# (background), plus the switch flaps, the four kinds of forest goods (acorn, chestnut, mushroom, pine cone, gold acorn),
# a squirrel, a bear and a tanuki peeking over baskets, and a little bonfire. python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 89.9; TZ = 0.0      # straight down: frame row ~ 640 - y * 160
PXU = RES[1] / SCALE

def zfor(py, y):
    """world z that lands on frame row py for an object at depth y"""
    e = math.radians(ELEV); return TZ + ((RES[1] / 2 - py) / PXU - y * math.sin(e)) / math.cos(e)

def proj(x, y, z):
    e = math.radians(ELEV)
    return (RES[0] / 2 + x * PXU, RES[1] / 2 - ((y * math.sin(e)) + (z - TZ) * math.cos(e)) * PXU)

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def reset(transparent=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe6ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # warm kitchen light from above-left + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.7; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(-2, -3, 8))
    a = bpy.context.object; a.data.energy = 260; a.data.size = 8; a.data.color = srgb('#e0ecff')
    a.rotation_euler = (Vector((0, 0, 3)) - a.location).to_track_quat('-Z', 'Y').to_euler()
    e = math.radians(ELEV); d = 40
    loc = Vector((0, 0, 40))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (0, 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = SCALE; c.data.clip_end = 200; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = RES
    return sc

def mat(name, color, rough=0.75, spec=0.15, sss=0.0, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (0.5, 0.4, 0.3); b.inputs['Subsurface Scale'].default_value = 0.08
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(emit[0]), 1); b.inputs['Emission Strength'].default_value = emit[1]
    return m

def noise_mat(name, c1, c2, scale=6, rough=0.85, bump=0.3, lo=.35, hi=.7, detail=6):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .12
    return m

def wood(name, c1, c2):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.rings_direction = 'Z'
    wv.inputs['Scale'].default_value = 2.5; wv.inputs['Distortion'].default_value = 4; wv.inputs['Detail'].default_value = 3
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7; b.inputs['Specular IOR Level'].default_value = .15
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
def sphere(loc, scale, m, seg=32, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = scale; o.rotation_euler = rot; smooth(o); o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def cyl(loc, r, d, m, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; smooth(o); o.data.materials.append(m); return o
def bevel(o, w, seg=4):
    b = o.modifiers.new('b', 'BEVEL'); b.width = w; b.segments = seg; b.limit_method = 'NONE'; return o


def render(sc, name):
    if os.environ.get('META_ONLY'): return
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True); print('wrote', name, flush=True)

META = {}
SPR = {}

def sprite_cam(sc, scale, res, tz=0.0):
    """same elevation as the room camera, ortho, square; returns world (x, z) at y=0 -> sprite px"""
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(ELEV); d = 30; tgt = Vector((0, 0, tz)); loc = tgt + Vector((0, -math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
def side_cam(sc, scale, res, tz, tx=0.0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    loc = Vector((tx, -30, tz)); bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + (x - tx) * res / scale, 1), round(res / 2 - (z - tz) * res / scale, 1)]

def box(loc, sc_, m, bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sc_; o.data.materials.append(m)
    if bev: bevel(o, bev, 3)
    return o


PX = 160.0       # pixels per world unit; frame 720 x 1280 = 4.5 x 8 units; front view, x right, z up, origin at frame centre

def front(sc, w, h, c=(0, 0)):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(c[0], -30, c[1])); cam = bpy.context.object; cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(w, h) / PX; cam.data.clip_end = 100; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h

def light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, -10, 10)); s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
    s.rotation_euler = (math.radians(50), 0, math.radians(-30))
    bpy.ops.object.light_add(type='AREA', location=(3, -8, 2)); a = bpy.context.object; a.data.energy = 650; a.data.size = 9; a.data.color = srgb('#e4eeff')
    a.rotation_euler = (Vector((0, 0, 0)) - a.location).to_track_quat('-Z', 'Y').to_euler()

def tp(x, z): return [round(360 + x * PX, 1), round(640 - z * PX, 1)]

def branch(pts, r0, r1, m):
    cu = bpy.data.curves.new('br', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1; cu.bevel_resolution = 4; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for i, (p, q) in enumerate(zip(sp.bezier_points, pts)):
        p.co = q; p.handle_left_type = p.handle_right_type = 'AUTO'; p.radius = r0 + (r1 - r0) * i / (len(pts) - 1)
    o = bpy.data.objects.new('br', cu); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

PATHS = {'A': (360, 430), 'B': (190, 650), 'C': (530, 650), 'L1': (100, 900), 'L2': (280, 900), 'R1': (440, 900), 'R2': (620, 900)}
SEGS = [('A', 'B'), ('A', 'C'), ('B', 'L1'), ('B', 'L2'), ('C', 'R1'), ('C', 'R2')]
BINS = {'L1': 100, 'L2': 280, 'R1': 440, 'R2': 620}
def wu(p): return ((p[0] - 360) / PX, (640 - p[1]) / PX)

def plank(p0, p1, m, rail, ext0=-0.12, ext1=0.1):
    (x0, z0), (x1, z1) = wu(p0), wu(p1); dx, dz = x1 - x0, z1 - z0; L = math.hypot(dx, dz); ux, uz = dx / L, dz / L
    nx, nz = uz, -ux                                    # perpendicular pointing below the path (path goes down-left or down-right)
    if nz > 0: nx, nz = -nx, -nz
    off = 0.2; cx, cz = (x0 + x1) / 2 + nx * off, (z0 + z1) / 2 + nz * off
    a = math.atan2(dz, dx)
    o = box((cx - ux * (ext0 - ext1) / 2, 0.3, cz - uz * (ext0 - ext1) / 2), (L + ext0 + ext1, 0.5, 0.13), m, 0.02); o.rotation_euler = (0, -a, 0)
    r = box((cx - ux * (ext0 - ext1) / 2 - nx * 0.02, -0.0, cz - uz * (ext0 - ext1) / 2 - nz * 0.02), (L + ext0 + ext1, 0.04, 0.2), rail, 0.01); r.rotation_euler = (0, -a, 0)
    # legs down to the ground
    for t in (0.25, 0.8):
        lx, lz = x0 + dx * t + nx * off, z0 + dz * t + nz * off
        box((lx, 0.45, (lz + -3.0) / 2), (0.06, 0.06, lz + 3.0), rail, 0.01)

def build_bg():
    sc = reset(False); light(sc); front(sc, 720, 1280)
    sky = bpy.data.materials.new('sky'); sky.use_nodes = True; nt = sky.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    em = nt.nodes.new('ShaderNodeEmission'); tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#f6e2b4'), 1); r.color_ramp.elements[1].color = (*srgb('#a6d0ea'), 1)
    r.color_ramp.elements[0].position = 0.3; nt.links.new(sx.outputs['Y'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 9, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (6, 10, 1); o.data.materials.append(sky)
    rnd = random.Random(4)
    # far forest: rounded trees in autumn colours
    cols = [('#c8783a', '#d88a44'), ('#d8a43a', '#e4b44a'), ('#8a9a44', '#9aaa4e'), ('#b85a32', '#c86a3c')]
    tm = [noise_mat('ft%d' % i, a, b, 4, 0.9, 0.3) for i, (a, b) in enumerate(cols)]
    trunk = noise_mat('trk', '#6a4a32', '#7a5a3a', 8, 0.9, 0.4)
    for i in range(11):
        x = -2.6 + i * 0.52 + rnd.uniform(-.1, .1); z = rnd.uniform(-0.6, 0.4); s = rnd.uniform(.55, .8)
        cyl((x, 7, z - 1.4), 0.08, 2.4, trunk, 12)
        sphere((x, 7 - i * 0.01, z), (s, 0.4, s * 1.15), tm[i % 4], 32)
    # ground with a mossy band and a few big leaves
    box((0, 3, -3.3), (8, 6, 1.6), noise_mat('gnd', '#b89058', '#c8a066', 6, 0.95, 0.3), 0)
    box((0, 1.2, -2.48), (8, 3, 0.05), noise_mat('moss', '#8a9a48', '#9aaa52', 8, 0.95, 0.3), 0)
    # the hopper at the top: a hollow log on a branch
    bark = noise_mat('bark', '#7a5636', '#8a6640', 10, 0.9, 0.5)
    x, z = wu((360, 175))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.2, radius2=0.62, depth=0.55, location=(x, 0.6, z + 0.25), rotation=(0, 0, math.radians(45))); o = bpy.context.object
    o.data.materials.append(wood('hop', '#b07a48', '#c08a54')); bevel(o, 0.03, 3)
    box((x, 0.6, z + 0.55), (0.92, 0.6, 0.06), wood('hopr', '#8a5a34', '#9a6a3e'), 0.02)
    box((x - 1.6, 0.9, z + 0.5), (3.2, 0.2, 0.14), bark, 0.04)
    # planks
    wood_ = wood('plank', '#c8945a', '#d8a46a'); rail = wood('rail', '#8a5a34', '#9a6a3e')
    for a, b in SEGS: plank(PATHS[a], PATHS[b], wood_, rail)
    # switch hubs
    for k in ('A', 'B', 'C'): x, z = wu(PATHS[k]); cyl((x, -0.1, z - 0.2), 0.11, 0.1, rail, 24, rot=(math.radians(90), 0, 0))
    render(sc, 'bg')
    META['paths'] = PATHS; META['bins'] = BINS; META['basketY'] = 1110

def build_flap():
    """lever pointing along +x from its pivot (sprite centre = pivot)"""
    sc = reset(True); light(sc); front(sc, 200, 200)
    m = wood('flap', '#e0a860', '#eab870'); r = mat('fr', '#c03a2a', 0.5)
    box((0.3, -0.05, 0), (0.58, 0.08, 0.1), m, 0.02)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.12, depth=0.06, location=(0.62, -0.08, 0), rotation=(math.radians(90), 0, math.radians(0))); o = bpy.context.object; o.rotation_euler = (math.radians(90), math.radians(90), 0); o.data.materials.append(r)
    cyl((0, -0.12, 0), 0.08, 0.06, r, 24, rot=(math.radians(90), 0, 0))
    render(sc, 'flap')

def item(name, kind):
    sc = reset(True); light(sc); front(sc, 80, 80)
    if kind in ('acorn', 'gold'):
        nut = mat('n' + name, '#b8743a' if kind == 'acorn' else '#e8b840', 0.35 if kind == 'acorn' else 0.25, 0.4 if kind == 'acorn' else 0.8)
        cap = noise_mat('c' + name, '#6a4a2a', '#7e5a34', 30, 0.9, 0.8) if kind == 'acorn' else mat('cg' + name, '#c89020', 0.3, 0.8)
        sphere((0, 0, -0.04), (0.14, 0.14, 0.17), nut, 40)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.04, depth=0.08, location=(0, 0, -0.22)); o = bpy.context.object; o.rotation_euler = (math.radians(180), 0, 0); o.data.materials.append(nut)
        sphere((0, 0, 0.08), (0.16, 0.16, 0.09), cap, 32); cyl((0, 0, 0.18), 0.02, 0.06, cap, 8)
    elif kind == 'kuri':
        m = mat('kuri', '#7a3e1e', 0.25, 0.5); b = mat('kurib', '#d8b07a', 0.8)
        o = sphere((0, 0, -0.02), (0.2, 0.12, 0.18), m, 40)
        sphere((0, -0.01, -0.15), (0.17, 0.1, 0.06), b, 24)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05, depth=0.08, location=(0, 0, 0.18)); o = bpy.context.object; o.data.materials.append(m)
    elif kind == 'kinoko':
        cap = mat('kcap', '#8a4e2a', 0.6, 0.2); stem = mat('kst', '#f0e2c4', 0.8)
        cyl((0, 0, -0.1), 0.06, 0.2, stem, 24)
        o = sphere((0, 0, 0.04), (0.2, 0.2, 0.11), cap, 40)
        sphere((0, -0.01, -0.0), (0.18, 0.18, 0.04), mat('gill', '#e8d4b0', 0.9), 32)
    elif kind == 'matsu':
        m = noise_mat('pc', '#8a5a32', '#9a6a3c', 10, 0.8, 0.4)
        for i in range(6):
            z = -0.18 + i * 0.065; rr = 0.15 * math.sin(math.pi * (i + 1) / 7.5) + 0.03
            for k in range(7):
                a = k * math.tau / 7 + i * 0.45; sphere((math.cos(a) * rr * .6, math.sin(a) * rr * .6, z), (rr * .55, rr * .45, 0.045), m, 12, rot=(0, -0.5, a))
        sphere((0, 0, 0), (0.09, 0.09, 0.19), m, 16)
    render(sc, name)

def animal(name, kind):
    sc = reset(True); light(sc); front(sc, 170, 150, (0, 0.05))
    eye = mat('eye', '#14100c', 0.4, 0.2); nose = mat('nose', '#3a2418', 0.4)
    if kind == 'risu':
        f = mat('rf', '#c8783a', 0.85); c = mat('rc', '#f4dcb4', 0.85)
        sphere((0, 0, 0), (0.34, 0.26, 0.3), f, 40)
        for s in (-1, 1): sphere((s * 0.22, 0, 0.3), (0.08, 0.05, 0.12), f, 20, rot=(0, s * -0.3, 0)); sphere((s * 0.22, -0.03, 0.29), (0.045, 0.03, 0.07), c, 16, rot=(0, s * -0.3, 0))
        sphere((0, -0.16, -0.08), (0.17, 0.12, 0.13), c, 32)
    elif kind == 'kuma':
        f = mat('kf', '#8a5a3a', 0.85); c = mat('kc', '#d8b48a', 0.85)
        sphere((0, 0, 0), (0.38, 0.28, 0.32), f, 40)
        for s in (-1, 1): sphere((s * 0.28, 0, 0.27), (0.1, 0.06, 0.1), f, 20); sphere((s * 0.28, -0.04, 0.27), (0.055, 0.03, 0.055), c, 16)
        sphere((0, -0.18, -0.08), (0.16, 0.12, 0.12), c, 32)
    else:
        f = mat('tf', '#9a8a74', 0.85); c = mat('tc', '#ece2d0', 0.85); d = mat('td', '#5e4e40', 0.85)
        sphere((0, 0, 0), (0.36, 0.27, 0.3), f, 40)
        for s in (-1, 1): sphere((s * 0.24, 0, 0.27), (0.09, 0.05, 0.09), d, 20); sphere((s * 0.13, -0.19, 0.03), (0.1, 0.06, 0.075), d, 20, rot=(0, s * 0.3, 0))
        sphere((0, -0.17, -0.1), (0.15, 0.12, 0.11), c, 32)
    for s in (-1, 1): sphere((s * 0.13, -0.26, 0.04), (0.032, 0.02, 0.032), eye, 16)
    sphere((0, -0.29, -0.06), (0.04, 0.025, 0.03), nose, 16)
    render(sc, name)

def build_kago():
    sc = reset(True); light(sc); front(sc, 170, 110)
    weave = noise_mat('weave', '#b8884a', '#cc9a58', 30, 0.85, 0.7, .3, .7, 4); rim = mat('brim', '#8a5a2e', 0.7)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.48, depth=0.4, location=(0, 0, -0.05)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        if v.co.z < 0: v.co.x *= 0.8; v.co.y *= 0.8
    tops = [f for f in bm.faces if all(v.co.z > 0.19 for v in f.verts)]; bmesh.ops.delete(bm, geom=tops, context='FACES')
    bm.to_mesh(o.data); bm.free(); o.data.materials.append(weave); o.modifiers.new('s', 'SOLIDIFY').thickness = 0.03
    bpy.ops.mesh.primitive_torus_add(major_radius=0.48, minor_radius=0.04, location=(0, 0, 0.15)); t = bpy.context.object; t.data.materials.append(rim)
    for ob in (o, t): ob.rotation_euler.x = math.radians(-14)
    render(sc, 'kago')

def build_fire():
    sc = reset(True); light(sc); front(sc, 170, 170, (0, 0.1))
    stone = noise_mat('st', '#8a8680', '#a09a92', 8, 0.9, 0.4); log = noise_mat('lg', '#6a4a2e', '#7a5a38', 10, 0.9, 0.5)
    for k in range(7): a = k * math.tau / 7; sphere((math.cos(a) * 0.38, math.sin(a) * 0.25 + 0.2, -0.3), (0.1, 0.08, 0.07), stone, 16)
    for a in (0.5, -0.5): cyl((0, 0.15, -0.22), 0.05, 0.6, log, 12, rot=(0, math.pi / 2 + a, 0.0))
    flame = mat('fl', '#f08a2a', 0.9, 0, emit=('#ffa040', 2.0)); flame2 = mat('fl2', '#ffd060', 0.9, 0, emit=('#ffe080', 2.5))
    for x, h, m in ((-0.1, 0.42, flame), (0.1, 0.36, flame), (0, 0.5, flame), (0, 0.3, flame2)):
        sphere((x * 1.5, 0.1, -0.1 + h * 0.6), (0.15 if m is flame else 0.09, 0.08, h * 0.75), m, 24)
    render(sc, 'fire')

JOBS = {'bg': build_bg, 'flap': build_flap, 'i_acorn': lambda: item('i_acorn', 'acorn'), 'i_gold': lambda: item('i_gold', 'gold'), 'i_kuri': lambda: item('i_kuri', 'kuri'),
        'i_kinoko': lambda: item('i_kinoko', 'kinoko'), 'i_matsu': lambda: item('i_matsu', 'matsu'),
        'a_risu': lambda: animal('a_risu', 'risu'), 'a_kuma': lambda: animal('a_kuma', 'kuma'), 'a_tanuki': lambda: animal('a_tanuki', 'tanuki'), 'kago': build_kago, 'fire': build_fire}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
