# Renders the layers for amamori.html: a tatami room seen from the front with a leaking wooden ceiling (stains over
# five leak points), a rainy shoji window, plus the catch containers (wooden oke, metal nabe, chawan bowl).
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


PX = 160.0       # pixels per world unit; frame 720 x 1280 = 4.5 x 8 units, origin at the frame centre (front view: x right, z up)

def front(sc, w, h, c=(0, 0)):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(c[0], -30, c[1])); cam = bpy.context.object; cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(w, h) / PX; cam.data.clip_end = 100; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h

def light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, -10, 10)); s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(35); s.data.color = srgb('#fff2e0')
    s.rotation_euler = (math.radians(50), math.radians(-25), 0)
    bpy.ops.object.light_add(type='AREA', location=(0, -12, 2)); a = bpy.context.object; a.data.energy = 1400; a.data.size = 14; a.data.color = srgb('#e2ecff')
    a.rotation_euler = (math.radians(90), 0, 0)

def fp(x, z): return [round(360 + x * PX, 1), round(640 - z * PX, 1)]
LEAKS = [-1.6, -0.8, 0.0, 0.8, 1.6]

def build_bg():
    sc = reset(False); light(sc); front(sc, 720, 1280)
    plaster = noise_mat('plaster', '#e6dac2', '#dccfb4', 18, 0.95, 0.2)
    box((0, 1.3, 0.2), (5, 0.2, 5.2), plaster, 0)
    # ceiling boards with wet stains above each leak
    cw = wood('ceil', '#7a5236', '#8a6040')
    for i in range(6): box((-2.25 + i * 0.9 + .45, 0.6, 3.35), (0.9, 0.4, 1.3), cw, 0.01)
    beam = wood('beam', '#4e3220', '#5a3a26'); box((0, 0.3, 2.62), (5, 0.6, 0.26), beam, 0.03)
    stain = mat('stain', '#4a2e1c', 0.9)
    for x in LEAKS:
        o = sphere((x, 0.38, 2.76), (0.26, 0.02, 0.1), stain, 24); o.scale = (0.26 + random.random() * .06, 0.02, 0.09)
    # shoji window with rain outside, a pillar either side
    outside = mat('rain', '#6f8292', 0.9, emit=('#8796a4', 0.35)); box((0, 1.15, 0.8), (3.0, 0.05, 2.1), outside, 0)
    sh = wood('shoji', '#d8c09a', '#e0c8a4')
    box((0, 0.95, 1.86), (3.1, 0.1, 0.08), sh, 0.01); box((0, 0.95, -0.26), (3.1, 0.1, 0.08), sh, 0.01)
    for i in range(5): box((-1.5 + i * 0.75, 0.95, 0.8), (0.05, 0.08, 2.1), sh, 0)
    for j in range(1, 4): box((0, 0.95, -0.26 + j * 0.53), (3.0, 0.08, 0.04), sh, 0)
    pil = wood('pil', '#6a4630', '#76503a')
    for sx in (-1, 1): box((sx * 2.1, 0.6, 0.2), (0.3, 0.3, 5), pil, 0.02)
    # low wooden wainscot and the tatami floor
    box((0, 0.85, -1.6), (5, 0.2, 0.9), wood('koshi', '#8a6040', '#96704a'), 0.01)
    box((0, 0.5, -2.08), (5, 0.6, 0.08), beam, 0.01)
    tat = noise_mat('tatami', '#a4a46a', '#b0ae74', 80, 0.95, 0.4, .3, .7, 4)
    box((0, 0, -3.15), (5, 2, 2.1), tat, 0)
    render(sc, 'bg')
    META['leaks'] = [fp(x, 2.66)[0] for x in LEAKS]; META['drip_y'] = fp(0, 2.62)[1]; META['floor_y'] = fp(0, -2.6)[1]

def wet(sc):
    pass

def build_pot(name, kind):
    sc = reset(True); light(sc); front(sc, 256, 256, (0, 0.6))
    if kind == 'oke':
        w = wood('oke', '#c89a60', '#d4a870')
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.5, radius2=0.62, depth=0.8, location=(0, 0, 0.4)); o = bpy.context.object; smooth(o); o.data.materials.append(w)
        hoop = mat('hoop', '#3a3a3e', 0.35, 0.6)
        for z, r in ((0.15, 0.53), (0.66, 0.6)):
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.03, location=(0, 0, z)); t = bpy.context.object; t.data.materials.append(hoop)
        for sx in (-1, 1): box((sx * 0.6, 0, 0.82), (0.08, 0.14, 0.2), w, 0.02)
    elif kind == 'nabe':
        m = mat('nabe', '#9aa0a8', 0.3, 0.8)
        cyl((0, 0, 0.27), 0.48, 0.54, m, 48); cyl((0, 0, 0.55), 0.5, 0.04, m, 48)
        bk = mat('bk', '#2e2a28', 0.6)
        for sx in (-1, 1): box((sx * 0.58, 0, 0.42), (0.2, 0.12, 0.08), bk, 0.03)
    else:
        m = mat('cha', '#e8dcc8', 0.35, 0.4); bl = mat('blu', '#3a5a8a', 0.4)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.36, location=(0, 0, 0.36)); o = bpy.context.object; smooth(o)
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.0], context='VERTS'); bm.to_mesh(o.data); bm.free()
        s = o.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.03; o.data.materials.append(m)
        cyl((0, 0, 0.04), 0.16, 0.08, m, 32)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.025, location=(0, 0, 0.24)); t = bpy.context.object; t.data.materials.append(bl)
    render(sc, name)

JOBS = {'bg': build_bg, 'oke': lambda: build_pot('oke', 'oke'), 'nabe': lambda: build_pot('nabe', 'nabe'), 'chawan': lambda: build_pot('chawan', 'chawan')}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
