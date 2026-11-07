# Renders the layers for bonsai.html: a tokonoma alcove seen from the front with a pine bonsai trunk in a glazed pot on a
# wooden stand (background), plus foliage pads (two shapes), a snipped twig and the scissors. python3 render.py <what> <outdir>
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

def build_bg():
    sc = reset(False); light(sc); front(sc, 720, 1280)
    # alcove: plaster back wall, darker side posts, tatami-coloured floor board
    box((0, 3, 0), (6, 0.2, 9), noise_mat('wall', '#e8dcc4', '#ded0b6', 4, 0.95, 0.1), 0)
    post = wood('post', '#5a3a24', '#6a4a2e')
    for sx in (-1, 1): box((sx * 2.2, 2.6, 0), (0.3, 0.3, 9), post, 0.01)
    box((0, 2.6, 3.95), (4.8, 0.3, 0.3), post, 0.01)
    box((0, 1.5, -3.4), (6, 3, 0.2), wood('floor', '#9a6a3e', '#aa7a48'), 0.01)
    # a hanging scroll with a soft painted moon (no text)
    box((-1.4, 2.85, 1.4), (0.7, 0.02, 2.4), mat('scroll', '#f2ead8', 0.9), 0); box((-1.4, 2.8, 2.62), (0.82, 0.06, 0.06), post, 0.01); box((-1.4, 2.8, 0.18), (0.82, 0.06, 0.06), post, 0.01)
    cyl((-1.4, 2.82, 1.9), 0.18, 0.01, mat('pmoon', '#e8b860', 0.8), 32, rot=(math.radians(90), 0, 0))
    # stand and pot
    st = wood('stand', '#4a2e1c', '#5a3a24')
    box((0, 0.6, -2.62), (2.6, 1.2, 0.14), st, 0.02)
    for sx in (-1, 1): box((sx * 1.15, 0.6, -2.95), (0.12, 1.0, 0.55), st, 0.01)
    pot = mat('pot', '#2e5a7a', 0.25, 0.4)
    bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=1.2, depth=0.5, location=(0, 0.6, -2.3), rotation=(0, 0, math.radians(45))); o = bpy.context.object
    o.scale = (1, 0.45, 1); o.data.materials.append(pot); bevel(o, 0.05, 4)
    box((0, 0.6, -2.04), (1.6, 0.6, 0.04), noise_mat('soil', '#5a4a3a', '#6a5a46', 20, 0.95, 0.5), 0)
    for sx in (-1, 1): box((sx * 0.6, 0.6, -2.58), (0.16, 0.5, 0.06), pot, 0.02)
    # pine trunk and branches (the canopy pads are sprites)
    bark = noise_mat('bark', '#6a4a3a', '#7e5a46', 12, 0.9, 0.7)
    branch([(0.2, 0.6, -2.05), (0.5, 0.6, -1.3), (-0.2, 0.6, -0.5), (0.3, 0.6, 0.4), (0, 0.6, 1.5), (0.05, 0.6, 2.0)], 0.2, 0.06, bark)
    for pts in ([(-0.1, .6, -.5), (-.7, .6, -.3), (-1.3, .6, -.1), (-1.6, .6, -.3)], [(.25, .6, .3), (.9, .6, .2), (1.4, .6, -.1), (1.7, .6, -.4)],
                [(0, .6, 1.2), (-.6, .6, 1.4), (-1.2, .6, 1.3)], [(0.1, .6, 1.4), (.7, .6, 1.7), (1.2, .6, 1.6)], [(.4, .6, -1.2), (1.0, .6, -1.0), (1.4, .6, -.9)]):
        branch(pts, 0.08, 0.03, bark)
    sphere((0, 0.6, -2.0), (0.5, 0.3, 0.06), noise_mat('moss', '#6a8a3a', '#7a9a44', 14, 0.95, 0.4), 24)
    render(sc, 'bg')
    META['pot'] = tp(0, -2.3)

def pine_mat():
    m = bpy.data.materials.get('pine')
    if m: return m
    m = noise_mat('pine', '#3e6e3a', '#5a8a44', 9, 0.85, 0.9, .3, .7, 8); return m

def build_pad(name, seed, w, h):
    sc = reset(True); light(sc); front(sc, int(w * PX + 30), int(w * PX + 30))
    rnd = random.Random(seed); m = pine_mat()
    for k in range(16):
        a = rnd.uniform(0, math.pi); rr = rnd.uniform(0.2, 1.0)
        x = math.cos(a) * rr * w * 0.42; z = math.sin(a) * rr * h * 0.55 - h * 0.18
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, location=(x, rnd.uniform(-.05, .05), z)); o = bpy.context.object
        tx = bpy.data.textures.new('pd%d' % k, 'CLOUDS'); tx.noise_scale = 0.06; d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.03
        s = rnd.uniform(.16, .24); o.scale = (s * 1.3, s, s * 0.8); smooth(o); o.data.materials.append(m)
    render(sc, name)

def build_twig():
    sc = reset(True); light(sc); front(sc, 70, 70)
    rnd = random.Random(3); m = pine_mat()
    cyl((0, 0, 0), 0.015, 0.3, mat('tw', '#6a4a3a', 0.8), 8, rot=(0, math.radians(60), 0))
    for k in range(5): sphere((rnd.uniform(-.1, .1), 0, rnd.uniform(-.05, .08)), (0.08, 0.06, 0.05), m, 12)
    render(sc, 'twig')

def build_scissors():
    sc = reset(True); light(sc); front(sc, 140, 140)
    steel = mat('steel', '#b8bcc4', 0.25, 0.8); hnd = mat('hnd', '#c04a3a', 0.5)
    for s_ in (-1, 1):
        o = box((0.18, 0, s_ * 0.02), (0.36, 0.03, 0.05), steel, 0.01); o.rotation_euler = (0, s_ * math.radians(14), 0)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.025, location=(-0.16, 0, s_ * 0.09), rotation=(math.radians(90), 0, 0)); t = bpy.context.object; t.data.materials.append(hnd)
    cyl((0, -0.03, 0), 0.025, 0.02, steel, 16, rot=(math.radians(90), 0, 0))
    render(sc, 'scissors')

JOBS = {'bg': build_bg, 'pad0': lambda: build_pad('pad0', 1, 0.75, 0.45), 'pad1': lambda: build_pad('pad1', 2, 0.7, 0.42), 'twig': build_twig, 'scissors': build_scissors}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
