# Renders the layers for mizukiri.html: a calm pond seen from the bank behind the cat (perspective camera low over the
# water; the sky is left transparent and painted by the game), plus stone and lily-pad sprites (top-down ortho).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 5.0; TZ = 0.0      # almost level: frame row ~ 640 - z * 160
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#e4eeff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
    # afternoon sun from the front-left, a soft sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(15); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(40), math.radians(-30), math.radians(160)))
    bpy.ops.object.light_add(type='AREA', location=(0, -4, 6))
    a = bpy.context.object; a.data.energy = 400; a.data.size = 8; a.data.color = srgb('#e0ecff')
    a.rotation_euler = (Vector((0, 2, 0)) - a.location).to_track_quat('-Z', 'Y').to_euler()
    e = math.radians(ELEV); d = 40
    tgt = Vector((0, 0, TZ)); loc = tgt + Vector((0, -math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
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

HC = 1.6; PITCH = 8.0; LENS = 30.0; F = LENS / 36.0 * RES[1]
def persp_cam(sc):
    """camera HC above the water at the bank, looking along +y, pitched down PITCH degrees"""
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, 0, HC)); c = bpy.context.object; c.rotation_euler = (math.radians(90 - PITCH), 0, 0)
    c.data.type = 'PERSP'; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 36; c.data.lens = LENS; c.data.clip_end = 600; sc.camera = c
def pproj(x, y, z):
    p = math.radians(PITCH); dep = y * math.cos(p) - (z - HC) * math.sin(p); up = y * math.sin(p) + (z - HC) * math.cos(p)
    return [round(RES[0] / 2 + F * x / dep, 1), round(RES[1] / 2 - F * up / dep, 1)]

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o

SHORE = 2.9; FAR = 70.0
def build_bg():
    sc = reset(True); persp_cam(sc)
    water = mat('water', '#5aa8c8', 0.22, 0.35)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 60, 0)); o = bpy.context.object; o.scale = (300, 140, 1); o.data.materials.append(water); o.visible_diffuse = False   # no blue bounce onto the cat
    # near bank: grass with a row of round stones at the water's edge, reeds at both sides
    grass = noise_mat('grass', '#6aa84a', '#86c060', 9, 0.9, 0.3); stone = noise_mat('stone', '#8a8a86', '#a8a8a2', 8, 0.85, 0.4)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, SHORE - 3, 0.0)); o = bpy.context.object; o.scale = (20, 6, 0.24); o.data.materials.append(grass); bevel(o, 0.08, 3); o.visible_diffuse = False   # no green bounce onto the cat
    random.seed(4)
    for k in range(26):
        x = -3.2 + k * 0.26 + random.uniform(-0.05, 0.05); sphere((x, SHORE + random.uniform(-0.05, 0.08), 0.06), (random.uniform(0.13, 0.2), 0.12, random.uniform(0.06, 0.1)), stone, 24)
    reed = mat('reed', '#5a8a3a', 0.8); cat_ = mat('cattail', '#7a4a2a', 0.85)
    for s_ in (-1, 1):
        for k in range(9):
            x = s_ * (0.95 + random.uniform(0, 0.4)); y = SHORE + random.uniform(-0.2, 0.9); h = random.uniform(1.0, 1.7)
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.025, depth=h, location=(x, y, h / 2)); r = bpy.context.object; r.rotation_euler = (random.uniform(-.1, .1), s_ * random.uniform(0, .18), 0); r.data.materials.append(reed)
            if k % 3 == 0: sphere((x + s_ * h * 0.06, y, h * 0.86), (0.035, 0.035, 0.12), cat_, 12)
    # far shore: soft hills, round trees and blue mountains
    hill = noise_mat('hill', '#5a9a4a', '#6aaa54', 3, 0.95, 0.2); tree = noise_mat('tree', '#3e7a3a', '#54924a', 6, 0.95, 0.5); mt = mat('mt', '#8aa8c8', 0.95)
    for k in range(9):
        x = -60 + k * 15 + random.uniform(-4, 4); sphere((x, FAR + random.uniform(0, 8), -1.5), (random.uniform(12, 18), 8, random.uniform(3.2, 4.6)), hill, 48)
    for k in range(30):
        x = -45 + k * 3.1 + random.uniform(-1, 1); y = FAR - 4 + random.uniform(0, 4); r = random.uniform(1.2, 2.0)
        sphere((x, y, r * 0.9), (r, r, r * 1.15), tree, 24)
    for k in range(5):
        x = -150 + k * 75 + random.uniform(-15, 15); sphere((x, 260, -10), (70, 30, random.uniform(28, 42)), mt, 48)
    # the cat, seen from behind on the bank, right paw raised with a stone
    # warm white without subsurface: the green bank and blue water otherwise bounce a mint tint onto the fur
    cw = mat('catw', '#fff2e2', 0.9, 0.05); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#4a4248', 0.85, 0.1); inner = mat('inner', '#f0b8b0', 0.85)
    X, Y, Z = -0.3, 2.3, 0.42
    bs = (0.34, 0.3, 0.32); sphere((X, Y, Z), bs, cw, 64)
    paint_on((X, Y, Z), bs, co, (X - 0.28, Y + 0.05, Z + 0.15), (0.26, 0.4, 0.24))
    hl = (X, Y + 0.02, Z + 0.42); hs = (0.26, 0.22, 0.22); sphere(hl, hs, cw, 64)
    paint_on(hl, hs, cg, (hl[0] + 0.2, hl[1] - 0.05, hl[2] + 0.17), (0.24, 0.3, 0.2))
    for s_, m in ((-1, co), (1, cg)):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.085, depth=0.17, location=(hl[0] + s_ * 0.14, hl[1] + 0.02, hl[2] + 0.2)); e = bpy.context.object; e.rotation_euler = (math.radians(8), s_ * 0.35, 0); e.data.materials.append(m); smooth(e)
    # raised right paw (toward +x) and a curled tail
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=0.36, location=(X + 0.3, Y - 0.02, Z + 0.22)); ar = bpy.context.object; ar.rotation_euler = (0, math.radians(-38), 0); ar.data.materials.append(cw); smooth(ar)
    sphere((X + 0.41, Y - 0.03, Z + 0.37), (0.09, 0.085, 0.085), cw, 24)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.05; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    bp[0].co = (X - 0.15, Y - 0.2, Z - 0.25); bp[1].co = (X - 0.45, Y - 0.32, Z - 0.26); bp[2].co = (X - 0.55, Y - 0.25, Z + 0.02)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    render(sc, 'bg')
    META['cam'] = {'hc': HC, 'pitch': PITCH, 'f': F}; META['paw'] = pproj(X + 0.41, Y - 0.03, Z + 0.37); META['pawW'] = [X + 0.41, Y - 0.03, Z + 0.37]
    META['shore'] = SHORE; META['far'] = FAR - 6; META['horizon'] = pproj(0, 1e4, 0)[1]; META['edge'] = pproj(0, SHORE, 0)[1]

def build_stone():
    sc = reset(True)
    for name, col, sc_ in (('stone', '#8a8e96', (0.5, 0.36, 0.12)), ('stone2', '#a89a88', (0.46, 0.4, 0.13))):
        for o in list(sc.objects):
            if o.type == 'MESH': bpy.data.objects.remove(o)
        st = noise_mat('st' + name, col, '#b8bcc4' if name == 'stone' else '#c8b8a4', 9, 0.8, 0.3)
        sphere((0, 0, 0), sc_, st, 48)
        side_cam(sc, 1.2, 96, 0.0); render(sc, name)
    SPR['stone'] = {'res': 96, 'pxu': 80.0, 'len': 1.0}

def build_pad():
    sc = reset(True)   # a lily pad with a notch and a pink flower, from straight above
    pad = noise_mat('pad', '#4a8a3a', '#5aa048', 6, 0.7, 0.2); pink = mat('lotus', '#f4a0c0', 0.7); yel = mat('lc', '#f2d04a', 0.7)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.0, depth=0.04, location=(0, 0, 0)); p = bpy.context.object; p.data.materials.append(pad)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.6, -0.0, 0)); c = bpy.context.object; c.scale = (1.2, 0.18, 0.2); c.rotation_euler = (0, 0, 0.0); c.hide_render = True
    bo = p.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'DIFFERENCE'
    for k in range(8):
        a = k / 8 * math.tau; sphere((math.cos(a) * 0.16 - 0.3, math.sin(a) * 0.16 + 0.2, 0.12), (0.16, 0.08, 0.07), pink, 16, rot=(0, 0, a))
    sphere((-0.3, 0.2, 0.16), (0.08, 0.08, 0.05), yel, 16)
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, 0, 20)); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.3; sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 192; render(sc, 'pad')
    SPR['pad'] = {'res': 192, 'r': 192 / 2.3}

JOBS = {'bg': build_bg, 'stone': build_stone, 'pad': build_pad}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}
json.dump(meta, open(MP, 'w'))
