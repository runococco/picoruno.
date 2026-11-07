# Renders the layers for zenmai.html: a low wooden table seen from straight above on tatami, three tin wind-up toys,
# a coiled straw trivet used as the target, a teacup and a mikan as obstacles.
# python3 render.py <what> <outdir>
# python3 render.py <what> <outdir>
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

def disc(loc, r, m, depth=0.01, verts=48):
    """flat painted disc facing the camera (-y)"""
    return cyl(loc, r, depth, m, verts, rot=(math.radians(90), 0, 0))

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o
def box(loc, sc_, m, bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sc_; o.data.materials.append(m); bevel(o, bev, 3); return o
def tp(x, y): return [round(RES[0] / 2 + x * PXU, 1), round(RES[1] / 2 - y * PXU, 1)]

def top_cam(sc, scale, res):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, 0, 30)); c = bpy.context.object; c.rotation_euler = (0, 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res

TX0, TX1, TY0, TY1 = -2.05, 2.05, -3.6, 3.2     # table top, world units

def planks():
    m = bpy.data.materials.new('planks'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (6, 0.6, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 5; wv.inputs['Detail'].default_value = 4; wv.inputs['Detail Scale'].default_value = 1.5
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#b07a48'), 1); r.color_ramp.elements[1].color = (*srgb('#c28c58'), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.75; b.inputs['Specular IOR Level'].default_value = .12
    return m

def build_bg():
    sc = reset(False)
    tat = noise_mat('tatami', '#c9c48a', '#d8d29a', 40, 0.9, 0.25)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.8)); o = bpy.context.object; o.scale = (8, 10, 1); o.data.materials.append(tat)
    border = mat('heri', '#3d5a4a', 0.8)
    for x in (-3.3, 3.3):
        box((x, 0, -0.79), (0.18, 10, 0.02), border, 0.005)
    for y in (-3.9, 3.95):
        box((0, y, -0.785), (10, 0.03, 0.02), mat('seam', '#b4ae76', 0.9), 0.005)
    tb = planks()
    box(((TX0 + TX1) / 2, (TY0 + TY1) / 2, -0.15), (TX1 - TX0, TY1 - TY0, 0.3), tb, 0.08)
    rim = mat('rim', '#8a5a32', 0.6)
    for k in (-1, 0, 1):   # plank seams
        box((k * (TX1 - TX0) / 4, (TY0 + TY1) / 2, 0.002), (0.012, TY1 - TY0 - 0.1, 0.004), mat('seam2', '#7a4c28', 0.8), 0.001)
    for (x0, x1, y0, y1) in ((TX0, TX1, TY1 - 0.06, TY1), (TX0, TX1, TY0, TY0 + 0.06)):
        box(((x0 + x1) / 2, (y0 + y1) / 2, 0.005), (x1 - x0, y1 - y0, 0.01), rim, 0.004)
    # zabuton peeking at the bottom corners, a tea tray corner at the top right off the table
    zab = noise_mat('zabuton', '#c8504a', '#d86a5a', 8, 0.95, 0.15)
    for x in (-2.6, 2.6):
        o = box((x, -3.95, -0.6), (1.5, 1.5, 0.2), zab, 0.18); o.rotation_euler = (0, 0, math.radians(12 if x > 0 else -10))
    render(sc, 'bg')
    META['table'] = [*tp(TX0, TY1), (TX1 - TX0) * PXU, (TY1 - TY0) * PXU]

def key(m, x, y, z, rot=0):
    """brass wind-up key sticking out of the toy's back, bows lying flat so it reads from above"""
    cyl((x, y + 0.03, z), 0.025, 0.14, m, 16, rot=(math.radians(90), 0, 0))
    for s in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.02, location=(x + s * 0.065, y - 0.05, z)); t = bpy.context.object; t.scale = (1, 0.8, 1); smooth(t); t.data.materials.append(m)
    sphere((x, y - 0.05, z), (0.03, 0.03, 0.02), m, 16)

def eyes(x, y, z, dx, r=0.03):
    blk = mat('blk', '#1e1410', 0.6, 0.05)
    for s in (-1, 1): sphere((x + s * dx, y, z), (r, r, r * .6), blk, 16)

def build_toy(name):
    sc = reset(True); top_cam(sc, 1.0, 160)
    metal = mat('brass', '#d8a83a', 0.45, 0.3)
    org = mat('beak', '#f08a2a', 0.6)
    if name == 'hiyoko':
        y_ = mat('hiyoko', '#ffd84a', 0.7, 0.1)
        sphere((0, -0.02, 0.15), (0.2, 0.24, 0.17), y_, 48)
        sphere((0, 0.14, 0.28), (0.13, 0.12, 0.11), y_, 40)
        for s in (-1, 1): sphere((s * 0.18, -0.04, 0.16), (0.06, 0.13, 0.05), y_, 24, rot=(0, 0, s * -0.3))
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.04, depth=0.09, location=(0, 0.28, 0.28)); o = bpy.context.object; o.rotation_euler = (math.radians(-90), 0, 0); o.data.materials.append(org)
        eyes(0, 0.2, 0.37, 0.055)
        for s in (-1, 1): sphere((s * 0.08, 0.17, 0.03), (0.04, 0.07, 0.02), org, 16)
        key(metal, 0, -0.3, 0.2)
    elif name == 'pengin':
        nv = mat('navy', '#2f3f62', 0.6, 0.15); wh = mat('white', '#f6f2ea', 0.7)
        sphere((0, -0.02, 0.17), (0.19, 0.22, 0.18), nv, 48)
        sphere((0, 0.13, 0.3), (0.13, 0.11, 0.1), nv, 40)
        sphere((0, 0.17, 0.31), (0.1, 0.075, 0.07), wh, 32)
        paint_on((0, -0.02, 0.17), (0.19, 0.22, 0.18), wh, (0, 0.2, 0.12), (0.15, 0.14, 0.2))
        for s in (-1, 1): sphere((s * 0.19, -0.02, 0.14), (0.04, 0.14, 0.04), nv, 24, rot=(0, 0, s * -0.4))
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.035, depth=0.08, location=(0, 0.26, 0.31)); o = bpy.context.object; o.rotation_euler = (math.radians(-90), 0, 0); o.data.materials.append(org)
        eyes(0, 0.19, 0.38, 0.05)
        key(metal, 0, -0.28, 0.2)
    else:  # kaeru
        g = mat('frog', '#6cc05a', 0.6, 0.15); bel = mat('frogb', '#c8e89a', 0.7)
        sphere((0, -0.02, 0.12), (0.22, 0.24, 0.12), g, 48)
        for s in (-1, 1):
            sphere((s * 0.1, 0.14, 0.2), (0.07, 0.07, 0.07), g, 32)
            sphere((s * 0.1, 0.15, 0.27), (0.03, 0.03, 0.02), mat('blk', '#1e1410', 0.6, 0.05), 16)
            sphere((s * 0.22, 0.12, 0.05), (0.05, 0.1, 0.03), g, 24, rot=(0, 0, s * -0.6))
            sphere((s * 0.22, -0.18, 0.05), (0.06, 0.13, 0.03), g, 24, rot=(0, 0, s * 0.5))
        paint_on((0, -0.02, 0.12), (0.22, 0.24, 0.12), bel, (0, -0.02, 0.3), (0.12, 0.14, 0.12))
        key(metal, 0, -0.3, 0.16)
    render(sc, name)

def build_target():
    sc = reset(True); top_cam(sc, 2.4, 384)
    cols = ['#e8d6a0', '#f2c0b0', '#e8d6a0', '#e88a6a', '#e8d6a0', '#d8483a']
    # coiled straw trivet: rings of rope, three coloured scoring bands
    rings = [(1.1, 0.65, '#efe0b0'), (0.65, 0.3, '#f4b8a0'), (0.3, 0.0, '#e0584a')]
    for (ro, ri, c) in rings:
        m = noise_mat('straw' + c, c, c, 30, 0.9, 0.4, .3, .7)
        n = max(1, int((ro - ri) / 0.06))
        for k in range(n):
            r = ro - (k + .5) * (ro - ri) / n
            if r < 0.04:
                sphere((0, 0, 0.03), (0.05, 0.05, 0.03), m, 24); continue
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=(ro - ri) / n * 0.55, major_segments=96, minor_segments=12, location=(0, 0, 0.0)); t = bpy.context.object; smooth(t); t.data.materials.append(m)
    render(sc, 'target')

def build_cup():
    sc = reset(True); top_cam(sc, 0.8, 128)
    gl = mat('yunomi', '#5f7f8a', 0.6, 0.15); tea = mat('tea', '#a8b85a', 0.6, 0.1)
    cyl((0, 0, 0.2), 0.27, 0.4, gl, 64)
    cyl((0, 0, 0.395), 0.23, 0.02, tea, 64)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.025, major_segments=64, location=(0, 0, 0.4)); t = bpy.context.object; smooth(t); t.data.materials.append(gl)
    render(sc, 'cup')

def build_mikan():
    sc = reset(True); top_cam(sc, 0.8, 128)
    m = noise_mat('mikan', '#f39a2a', '#f7aa3a', 60, 0.6, 0.5)
    sphere((0, 0, 0.18), (0.24, 0.24, 0.19), m, 48)
    sphere((0, 0, 0.36), (0.04, 0.04, 0.02), mat('heta', '#5a7a2a', 0.8), 16)
    o = sphere((0.06, 0.03, 0.37), (0.08, 0.035, 0.012), mat('leaf', '#4f9a3a', 0.6), 16, rot=(0, 0, 0.5))
    render(sc, 'mikan')

JOBS = {'bg': build_bg, 'hiyoko': lambda: build_toy('hiyoko'), 'pengin': lambda: build_toy('pengin'), 'kaeru': lambda: build_toy('kaeru'),
        'target': build_target, 'cup': build_cup, 'mikan': build_mikan}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
