# Renders the layers for toubun.html: a kitchen counter seen from straight above with a big hinoki cutting board,
# plus the vegetables to cut (cucumber, carrot, daikon, negi, kamaboko) laid horizontally, ends recorded in scene.json.
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

def box(loc, sc_, m, bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sc_; o.data.materials.append(m)
    if bev: bevel(o, bev, 3)
    return o


PX = 160.0       # pixels per world unit; frame 720 x 1280 = 4.5 x 8 units, origin at the frame centre

def top(sc, w, h, c=(0, 0)):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(c[0], c[1], 30)); cam = bpy.context.object; cam.rotation_euler = (0, 0, 0)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(w, h) / PX; cam.data.clip_end = 100; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h

def light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(30); s.data.color = srgb('#fff4e2')
    s.rotation_euler = (math.radians(30), math.radians(-20), 0)
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 12)); a = bpy.context.object; a.data.energy = 900; a.data.size = 12; a.data.color = srgb('#e6f0ff')

def tp(x, y): return [round(360 + x * PX, 1), round(640 - y * PX, 1)]

def blade(loc, h, lean, m, w=0.05):
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=w, depth=h, location=(loc[0], loc[1], h / 2)); o = bpy.context.object
    o.rotation_euler = (lean[0], lean[1], 0); o.scale = (1, 0.35, 1); o.data.materials.append(m); return o

def build_bg():
    sc = reset(False); light(sc); top(sc, 720, 1280)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (5, 9, 1); o.data.materials.append(noise_mat('counter', '#8a6a4a', '#7e6044', 10, 0.8, 0.2))
    # tiled backsplash strip at the top
    tile = mat('tile', '#e8eef0', 0.4, 0.3)
    for i in range(-3, 4):
        for j in range(2): box((i * 0.7, 3.65 + j * 0.42, 0.03), (0.66, 0.38, 0.04), tile, 0.02)
    box((0, 0.1, 0.09), (4.2, 3.0, 0.16), noise_mat('board', '#e6c89a', '#dcbc8c', 22, 0.85, 0.15), 0.06)
    # a small bowl, a salt pot and a folded cloth around the board
    cyl((1.55, -2.55, 0.12), 0.42, 0.22, mat('bowl', '#3a5a8a', 0.35, 0.4), 48); cyl((1.55, -2.55, 0.2), 0.34, 0.1, mat('bowlin', '#f2ece2', 0.35), 48)
    cyl((-1.6, -2.6, 0.15), 0.24, 0.3, mat('salt', '#f0e6d6', 0.4), 32)
    box((-0.2, -2.7, 0.04), (1.2, 0.7, 0.05), noise_mat('cloth', '#d8604a', '#e07058', 14, 0.95, 0.2), 0.02)
    render(sc, 'bg')
    META['board'] = [tp(-2.1, 1.6), tp(2.1, -1.4)]

def veg_cam(sc): top(sc, 640, 200)

def build_veg(name):
    sc = reset(True); light(sc); veg_cam(sc)
    if name == 'kyuri':
        m = noise_mat('kyuri', '#3e7a2e', '#5a9a3e', 30, 0.55, 0.5)
        sphere((0, 0, 0.2), (1.75, 0.22, 0.2), m, 48); half = 1.75
    elif name == 'ninjin':
        m = noise_mat('ninjin', '#e8782a', '#f08a3a', 25, 0.6, 0.4)
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.3, radius2=0.04, depth=3.2, location=(0, 0, 0.3), rotation=(0, math.radians(90), 0))
        o = bpy.context.object; smooth(o); o.data.materials.append(m)
        sphere((-1.6, 0, 0.3), (0.06, 0.3, 0.3), m, 32)
        g = mat('leaf', '#4e8a3a', 0.7)
        for a in (-0.25, 0, 0.25): cyl((-1.82, a * 0.4, 0.3), 0.05, 0.4, g, 12, rot=(0, math.radians(90), a))
        half = 1.6
    elif name == 'daikon':
        m = noise_mat('daikon', '#f4f0e6', '#ebe6da', 25, 0.5, 0.3)
        cyl((0.1, 0, 0.3), 0.34, 3.2, m, 48, rot=(0, math.radians(90), 0))
        sphere((1.7, 0, 0.3), (0.06, 0.34, 0.34), m, 32)
        cyl((-1.45, 0, 0.3), 0.345, 0.4, mat('dtop', '#c8d8a0', 0.6), 48, rot=(0, math.radians(90), 0))
        sphere((-1.65, 0, 0.3), (0.05, 0.345, 0.345), mat('dtop', '#c8d8a0', 0.6), 32); half = 1.7
    elif name == 'negi':
        cyl((0.55, 0, 0.15), 0.13, 2.4, mat('negiw', '#f2f2e8', 0.5), 32, rot=(0, math.radians(90), 0))
        cyl((-1.25, 0, 0.15), 0.13, 1.2, mat('negig', '#5a9a3a', 0.6), 32, rot=(0, math.radians(90), 0))
        sphere((1.75, 0, 0.15), (0.04, 0.13, 0.13), mat('negiw', '#f2f2e8', 0.5), 16); half = 1.85
    else:   # kamaboko on its board
        box((0, 0, 0.06), (3.0, 0.62, 0.1), wood('kb', '#e0c090', '#e8cca0'), 0.01)
        o = cyl((0, 0, 0.12), 0.3, 2.9, mat('kama', '#f6f0ea', 0.5), 48, rot=(0, math.radians(90), 0)); o.scale = (1, 1, 1)
        box((0, 0.27, 0.2), (2.9, 0.06, 0.2), mat('pink', '#e8708a', 0.5), 0.02); half = 1.5
    render(sc, name)
    META.setdefault('veg', {})[name] = [round(320 - half * PX, 1), round(320 + half * PX, 1)]

JOBS = {'bg': build_bg}
for v in ('kyuri', 'ninjin', 'daikon', 'negi', 'kamaboko'): JOBS[v] = (lambda v=v: build_veg(v))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
