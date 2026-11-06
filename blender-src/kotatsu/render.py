# Renders the layers for kotatsu.html: the kotatsu table seen from straight above (full frame) and the
# mikan / yuzu / cat-paw sprites (same top-down camera).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 89.9; TZ = 0.0     # straight down: frame row = 640 - y * 160
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff0dc'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # cosy room light from above-front + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 600; a.data.size = 8; a.data.color = srgb('#ffe8d0')
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
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + x * res / scale, 1), round(res / 2 - (z - tz) * math.cos(e) * res / scale, 1)]

TABLE = (3.7, 6.1)        # table top size (x, y)
TY = -0.35                # table centre y
TARGET = (0.0, 1.6)       # target centre on the table

def build_bg():
    sc = reset(False)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#e8d8c0'), 1)
    # tatami under everything
    tat = noise_mat('tatami', '#c8b878', '#d8c888', 60, 0.8, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.6)); f = bpy.context.object; f.scale = (12, 12, 1); f.data.materials.append(tat)
    # futon spreading out from under the table: a puffy quilt with a pattern
    q1 = noise_mat('quilt', '#c84a40', '#d85a4a', 12, 0.95, 0.4); q2 = mat('quilt2', '#f0e0c8', 0.95, 0.1); q3 = mat('quilt3', '#3a5a9a', 0.9, 0.1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, TY, -0.35)); o = bpy.context.object; o.scale = (TABLE[0] + 1.4, TABLE[1] + 1.4, 0.3); o.data.materials.append(q1); bevel(o, 0.25, 6)
    random.seed(3)
    for k in range(60):
        x = (random.random() - 0.5) * (TABLE[0] + 1.3); y = TY + (random.random() - 0.5) * (TABLE[1] + 1.3)
        if abs(x) < TABLE[0] / 2 + 0.1 and abs(y - TY) < TABLE[1] / 2 + 0.1: continue
        sphere((x, y, -0.2), (0.12, 0.12, 0.02), q2 if k % 3 else q3, 16)
    # table top: warm wood with a darker rim
    top = noise_mat('tabletop', '#d8a868', '#cc9a5c', 3, 0.6, 0.1); rim = wood('rim', '#8a5a32', '#6a4020')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, TY, 0.0)); t = bpy.context.object; t.scale = (TABLE[0] + 0.24, TABLE[1] + 0.24, 0.1); t.data.materials.append(rim); bevel(t, 0.05, 4)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, TY, 0.02)); t = bpy.context.object; t.scale = (TABLE[0], TABLE[1], 0.1); t.data.materials.append(top)
    # target: a round woven mat with rings
    for r, c in ((0.95, '#3a6ab8'), (0.72, '#f6f0e0'), (0.48, '#d84a3a'), (0.2, '#f6f0e0')):
        cyl((TARGET[0], TARGET[1], 0.075 + (0.95 - r) * 0.004), r, 0.012, noise_mat('ring' + c, c, c, 80, 0.95, 0.3), 96)
    # throw line + hog line
    ln = mat('line', '#f6f0e0', 0.8)
    for y in (-2.55, 0.0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.075)); o = bpy.context.object; o.scale = (TABLE[0] - 0.2, 0.03, 0.005); o.data.materials.append(ln)
    # tea, a bowl of spare mikans and the cat waiting at the far side
    cup = mat('cup', '#5a8a6a', 0.4, 0.4); tea = mat('tea', '#9ab040', 0.2, 0.5)
    cyl((-1.55, -3.75, 0.2), 0.22, 0.3, cup, 32); cyl((-1.55, -3.75, 0.35), 0.19, 0.01, tea, 32)
    bowl = mat('bowl', '#2a4a7a', 0.4, 0.3); orange = noise_mat('mk', '#f08a20', '#f8a030', 40, 0.6, 0.4)
    cyl((1.55, -3.95, 0.12), 0.42, 0.16, bowl, 48)
    for (dx, dy) in ((-0.15, -0.1), (0.17, -0.05), (0.0, 0.17)): sphere((1.55 + dx, -3.95 + dy, 0.28), (0.16, 0.16, 0.14), orange, 24)
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); bk = mat('eye', '#1a1210', 0.9); pk = mat('catpk', '#f4a8a0', 0.8)
    cy = TY + TABLE[1] / 2 + 0.5
    sphere((0, cy + 0.35, 0.15), (0.6, 0.45, 0.35), cw, 48)                       # body under the futon edge
    sphere((0, cy, 0.4), (0.36, 0.32, 0.3), cw, 48)                               # head looking down at the table
    sphere((0.14, cy + 0.05, 0.62), (0.13, 0.12, 0.06), co, 24)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.11, depth=0.2, location=(s_ * 0.24, cy + 0.12, 0.66)); e = bpy.context.object; e.rotation_euler = (math.radians(-30), s_ * 0.35, 0); e.data.materials.append(co if s_ > 0 else cw); smooth(e)
        sphere((s_ * 0.13, cy - 0.11, 0.655), (0.042, 0.042, 0.02), bk, 16)     # face turned up toward the camera
        sphere((s_ * 0.21, cy - 0.2, 0.555), (0.06, 0.045, 0.02), pk, 12)
    sphere((0, cy - 0.21, 0.625), (0.032, 0.024, 0.015), pk, 8)
    render(sc, 'bg')
    META['table'] = [proj(-TABLE[0] / 2, TY + TABLE[1] / 2, 0)[0], proj(-TABLE[0] / 2, TY + TABLE[1] / 2, 0)[1], proj(TABLE[0] / 2, TY - TABLE[1] / 2, 0)[0], proj(TABLE[0] / 2, TY - TABLE[1] / 2, 0)[1]]
    META['target'] = proj(TARGET[0], TARGET[1], 0.08); META['rings'] = [0.95 * 160, 0.72 * 160, 0.48 * 160, 0.2 * 160]
    META['lines'] = [proj(0, -2.55, 0)[1], proj(0, 0.0, 0)[1]]

def build_fruit():
    sc = reset(True)   # mikan from above: dimpled peel, a little leaf and stem
    peel = noise_mat('peel', '#f08418', '#f8a030', 70, 0.55, 0.6)
    sphere((0, 0, 0), (0.22, 0.22, 0.18), peel, 48)
    cyl((0, 0, 0.17), 0.02, 0.02, mat('stem', '#6a7a3a', 0.7), 12)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(0.06, 0.04, 0.175)); l = bpy.context.object; l.scale = (0.09, 0.04, 0.01); l.rotation_euler = (0, 0, 0.6); l.data.materials.append(mat('leaf', '#3a8a3a', 0.6)); smooth(l)
    sprite_cam(sc, 0.5, 128); SPR['fruit'] = {'res': 128, 'pxu': 128 / 0.5, 'r': 0.22}
    render(sc, 'mikan')
    sc = reset(True)   # yuzu: bumpier, lemon-yellow
    peel = noise_mat('yuzu', '#e8c020', '#f4d848', 30, 0.6, 1.2)
    sphere((0, 0, 0), (0.22, 0.22, 0.17), peel, 48)
    cyl((0, 0, 0.16), 0.024, 0.03, mat('stem2', '#5a6a2a', 0.7), 12)
    sprite_cam(sc, 0.5, 128)
    render(sc, 'yuzu')
    sc = reset(True)   # the cat's front paw reaching in from the top
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); pk = mat('pad', '#f4a8a0', 0.8)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=0.8, location=(0, 0.42, 0)); a = bpy.context.object; a.rotation_euler = (math.radians(90), 0, 0); a.data.materials.append(cw); smooth(a)
    sphere((0, 0, 0), (0.15, 0.14, 0.1), cw, 32)
    for k in (-1, 0, 1): sphere((k * 0.075, -0.1, 0.05), (0.04, 0.035, 0.03), cw, 16)
    sphere((0.02, 0.35, 0.06), (0.1, 0.16, 0.08), mat('cato2', '#e8a050', 0.85, 0.1), 24)   # orange patch like the head
    sprite_cam(sc, 1.2, 160); SPR['paw'] = {'res': 160, 'pxu': 160 / 1.2, 'tip': [80.0, 80 + 0.14 * 160 / 1.2]}
    render(sc, 'paw')

JOBS = {'bg': build_bg, 'fruit': build_fruit}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
