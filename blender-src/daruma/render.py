# Renders the layers for daruma.html: a tatami room with a low table (side view) and the stack pieces:
# lacquered discs, a wooden cat head on top, the base disc and a wooden mallet.
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe6ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # warm afternoon light from above-left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 8; a.data.color = srgb('#e0ecff')
    a.rotation_euler = (Vector((0, 0, 3)) - a.location).to_track_quat('-Z', 'Y').to_euler()
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

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o

TABLE = -2.3
def build_bg():
    sc = reset(True)
    tatami = noise_mat('tatami', '#c8c47a', '#d6d28c', 30, 0.9, 0.25, .3, .7, 3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, -4.2)); o = bpy.context.object; o.scale = (14, 30, 1); o.data.materials.append(tatami); o.visible_diffuse = False
    # back wall: plaster, shoji panels with a wooden lattice, a wooden beam
    plaster = noise_mat('plaster', '#efe2c8', '#f6ecd8', 12, 0.95, 0.1); woodm = wood('beam', '#8a6040', '#a07450')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, 2), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (14, 16, 1); o.data.materials.append(plaster); o.visible_diffuse = False
    paper = mat('shoji', '#fbf6ea', 0.95, 0.05, emit=('#fff0d8', 0.18))
    for cx in (-2.3, 0.0, 2.3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, 7.9, 1.2)); o = bpy.context.object; o.scale = (2.2, 0.04, 5.6); o.data.materials.append(paper)
        for k in range(4):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(cx - 0.825 + k * 0.55, 7.85, 1.2)); o = bpy.context.object; o.scale = (0.05, 0.05, 5.6); o.data.materials.append(woodm)
        for k in range(8):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, 7.85, -1.6 + k * 0.8)); o = bpy.context.object; o.scale = (2.2, 0.05, 0.05); o.data.materials.append(woodm)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx + 1.12, 7.8, 1.2)); o = bpy.context.object; o.scale = (0.1, 0.1, 5.8); o.data.materials.append(woodm)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7.7, 4.15)); o = bpy.context.object; o.scale = (14, 0.3, 0.3); o.data.materials.append(woodm)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7.7, -1.75)); o = bpy.context.object; o.scale = (14, 0.3, 0.16); o.data.materials.append(woodm)
    koshi = wood('koshi', '#a87a52', '#b88a60')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7.75, -3.0)); o = bpy.context.object; o.scale = (14, 0.1, 2.5); o.data.materials.append(koshi); o.visible_diffuse = False
    # the low table we play on
    top = wood('table', '#9a6a44', '#b07c50')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.6, TABLE - 0.12)); o = bpy.context.object; o.scale = (5.6, 3.2, 0.24); bevel(o, 0.05)
    o.data.materials.append(top)
    for x in (-2.4, 2.4):
        for y in (-0.7, 1.9):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, (TABLE - 0.24 - 4.2) / 2)); o = bpy.context.object; o.scale = (0.3, 0.3, TABLE + 4.2 - 0.24); o.data.materials.append(top)
    # a small cushion and a teacup on the table edge for life
    zab = noise_mat('zab', '#d86a5a', '#e07a68', 10, 0.95, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.6, -2.2, -4.05)); o = bpy.context.object; o.scale = (1.6, 1.6, 0.3); bevel(o, 0.14, 6); o.data.materials.append(zab)
    cup = mat('cup', '#7aa8a0', 0.4, 0.3); tea = mat('tea', '#8aa848', 0.3, 0.4)
    cyl((2.1, 0.1, TABLE + 0.22), 0.26, 0.44, cup, 48); cyl((2.1, 0.1, TABLE + 0.43), 0.22, 0.02, tea, 48)
    render(sc, 'bg')
    META['table'] = proj(0, 0.6, TABLE)[1]

COLORS = {'red': '#d8483a', 'blue': '#3a78c8', 'yellow': '#f0b830', 'green': '#4aa860', 'purple': '#9a5ab8'}
R_BLOCK = 0.7; H_BLOCK = 0.48
def disc_sprite(name, color, bandc=None):
    sc = reset(True)
    m = mat('lac' + name, color, 0.35, 0.35) if bandc is not None or name != 'base' else wood('basew', '#b88a5a', '#c89a68')
    o = cyl((0, 0, 0), R_BLOCK, H_BLOCK, m, 96); bevel(o, 0.05)
    if bandc:
        cyl((0, 0, 0), R_BLOCK + 0.004, 0.06, mat('band' + name, bandc, 0.4, 0.3), 96)
    sprite_cam(sc, 1.6, 256); sc.render.resolution_x = 256; sc.render.resolution_y = 128
    c = sc.camera; c.data.ortho_scale = 1.6; render(sc, name)

def build_blocks():
    for k, v in COLORS.items(): disc_sprite('b_' + k, v, '#f4e8c8')
    disc_sprite('base', None)

def build_head():
    sc = reset(True)
    body = wood('headw', '#f2dcb4', '#f8e6c4'); blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8)
    patch = mat('patch', '#e8a050', 0.6, 0.2); patch2 = mat('patch2', '#4a4248', 0.6, 0.2)
    hs = (0.62, 0.55, 0.52); hl = (0, 0, 0.52); sphere(hl, hs, body, 64)
    paint_on(hl, hs, patch, (0.45, -0.3, 0.85), (0.4, 0.5, 0.4)); paint_on(hl, hs, patch2, (-0.5, -0.2, 0.9), (0.32, 0.5, 0.3))
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.2, depth=0.36, location=(s_ * 0.36, 0, 1.0)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.45, 0); e.data.materials.append(patch2 if s_ < 0 else patch); smooth(e)
        sphere((s_ * 0.2, -0.5, 0.56), (0.06, 0.03, 0.08), blk, 24)
    sphere((0, -0.54, 0.45), (0.045, 0.03, 0.035), pink, 16)
    side_cam(sc, 1.6, 256, 0.6); render(sc, 'head')

def build_mallet():
    sc = reset(True)
    w = wood('mallet', '#c89a68', '#d8aa78'); hw = wood('handle', '#9a6a44', '#aa7a50')
    o = cyl((0.55, 0, 0), 0.26, 0.62, w, 64, rot=(0, math.radians(90), 0)); bevel(o, 0.04)
    cyl((-0.25, 0, 0), 0.09, 1.1, hw, 32, rot=(0, math.radians(90), 0))
    side_cam(sc, 2.0, 256, 0.0, 0.0); render(sc, 'mallet')

JOBS = {'bg': build_bg, 'blocks': build_blocks, 'head': build_head, 'mallet': build_mallet}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
