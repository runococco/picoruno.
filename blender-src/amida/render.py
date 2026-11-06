# Renders the layers for amida.html: a desk seen from straight above with a big sheet of washi paper (the ladder lines are
# drawn by the game), a pencil, plus the cat token (face up) and the plates at the bottom of the ladder (top-down ortho).
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

PAPER = (0.0, 0.1, 4.0, 6.3)
def build_bg():
    sc = reset(True)
    desk = wood('desk', '#b88050', '#c89060'); box((0, 0, -0.6), (9, 12, 0.4), desk, 0.0)
    paper = noise_mat('washi', '#efe6d2', '#e8dcc4', 30, 0.95, 0.08)
    cx, cy, w, h = PAPER
    box((cx, cy, -0.36), (w, h, 0.02), paper, 0.005)
    # a pencil lying at the top right, an eraser at the top left
    pen = mat('pencil', '#e8b030', 0.6); tipw = mat('tipw', '#e8c898', 0.8); lead = mat('lead', '#3a3034', 0.7); pink = mat('eraser', '#f0a0a8', 0.8)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.07, depth=1.6, location=(0.9, 3.55, -0.28), rotation=(0, math.radians(90), math.radians(-6))); o = bpy.context.object; o.data.materials.append(pen)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.07, depth=0.22, location=(1.81, 3.46, -0.28), rotation=(0, math.radians(90), math.radians(-6))); o = bpy.context.object; o.data.materials.append(tipw)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.025, depth=0.07, location=(1.94, 3.445, -0.28), rotation=(0, math.radians(90), math.radians(-6))); o = bpy.context.object; o.data.materials.append(lead)
    box((-1.6, 3.55, -0.3), (0.5, 0.26, 0.14), pink, 0.04)
    render(sc, 'bg')
    META['paper'] = [*tp(cx - w / 2, cy + h / 2), w * PXU, h * PXU]

def build_cat():
    sc = reset(True)
    cw = mat('catw', '#fbf6ec', 0.85, 0.1); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#4a4248', 0.85, 0.1)
    blk = mat('eye', '#1a1210', 0.9, 0.0); pnk = mat('nose', '#e88a8a', 0.8)
    hs = (0.5, 0.42, 0.42); sphere((0, 0, 0), hs, cw, 64)
    paint_on((0, 0, 0), hs, cg, (0.38, 0.3, 0.1), (0.36, 0.4, 0.5)); paint_on((0, 0, 0), hs, co, (-0.42, 0.2, 0.1), (0.3, 0.36, 0.5))
    for s_, m in ((-1, co), (1, cg)):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.16, depth=0.3, location=(s_ * 0.3, 0.38, 0.05)); e = bpy.context.object; e.rotation_euler = (math.radians(-80), 0, s_ * -0.45); e.data.materials.append(m); smooth(e)
    for s_ in (-1, 1): sphere((s_ * 0.17, 0.02, 0.4), (0.06, 0.075, 0.03), blk, 24)
    sphere((0, -0.1, 0.41), (0.04, 0.03, 0.02), pnk, 16)
    for o2 in list(sc.objects):
        if o2.type == 'CAMERA': bpy.data.objects.remove(o2)
    bpy.ops.object.camera_add(location=(0, 0.05, 20)); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.3; sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 128; render(sc, 'cat')

def build_plates():
    for name in ('big', 'small', 'empty', 'dango'):
        sc = reset(True)
        plate = mat('plate', '#f8f4ee', 0.4, 0.25); rim = mat('rim', '#4a7ab8', 0.5)
        cyl((0, 0, 0), 0.5, 0.06, plate, 64)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.46, minor_radius=0.025, location=(0, 0, 0.04)); o = bpy.context.object; o.data.materials.append(rim)
        if name in ('big', 'small'):
            k = 1.0 if name == 'big' else 0.7; fish = mat('fish' + name, '#8aa8c8' if name == 'big' else '#e88a6a', 0.6, 0.2); dark = mat('fd', '#5a7898' if name == 'big' else '#c86a4a', 0.7)
            sphere((-0.04 * k, 0, 0.1), (0.3 * k, 0.13 * k, 0.07), fish, 32)
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.13 * k, depth=0.18 * k, location=(0.32 * k, 0, 0.1), rotation=(0, math.radians(-90), 0)); t = bpy.context.object; t.scale = (0.5, 1, 1); t.data.materials.append(dark)
            sphere((-0.22 * k, -0.04 * k, 0.16), (0.022, 0.022, 0.01), mat('eye', '#1a1210', 0.9), 12)
            for j in range(3): sphere((-0.02 * k + j * 0.08 * k, 0, 0.165), (0.02, 0.07 * k, 0.008), dark, 12)
        elif name == 'dango':
            for j, c in enumerate(('#f4a0b8', '#fbf6ec', '#9ad87a')): sphere((-0.18 + j * 0.18, 0, 0.12), (0.1, 0.1, 0.08), mat('dg' + c, c, 0.8), 24)
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.015, depth=0.75, location=(0.02, 0, 0.12), rotation=(0, math.radians(90), 0)); o = bpy.context.object; o.data.materials.append(mat('kushi', '#d8b880', 0.8))
        for o2 in list(sc.objects):
            if o2.type == 'CAMERA': bpy.data.objects.remove(o2)
        bpy.ops.object.camera_add(location=(0, 0, 20)); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.1; sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = 128; render(sc, 'plate_' + name)

JOBS = {'bg': build_bg, 'cat': build_cat, 'plates': build_plates}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
