# Renders the layers for kamo.html: a pond seen straight from above (banks with reeds and grass, a few lily pads,
# the straw nest on the bottom bank), plus the mother duck, ducklings (two paddle poses each) and drifting logs.
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
    # water: deep teal in the middle, lighter at the edges via a radial ramp, gentle ripple bump
    wm = bpy.data.materials.new('pond'); wm.use_nodes = True; nt = wm.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.42, 0.26, 1); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#7cc6c2'), 1); r.color_ramp.elements[1].color = (*srgb('#3c9aa6'), 1)
    nt.links.new(gr.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.06; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.15
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (5, 9, 1); o.data.materials.append(wm)
    # banks: grassy soil around the frame, a sandy shelf, the nest bank at the bottom
    grass = noise_mat('grass', '#7aae4e', '#90c060', 9, 0.95, 0.4)
    soil = noise_mat('soil', '#b89a6a', '#c8aa78', 10, 0.95, 0.3)
    def bank(pts, m, z):
        bm = bmesh.new(); vs = [bm.verts.new((x, y, z)) for x, y in pts]; bm.faces.new(vs); me = bpy.data.meshes.new('bk'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new('bk', me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
        so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.3; so.offset = 0; bevel(o, 0.08, 3); return o
    rnd = random.Random(5)
    def wavy(x0, x1, y, amp, n):
        return [(x0 + (x1 - x0) * i / n, y + amp * math.sin(i * 1.7) + rnd.uniform(-amp, amp) * 0.5) for i in range(n + 1)]
    # bottom bank with the nest
    bot = wavy(2.6, -2.6, -2.7, 0.12, 14); bank(bot + [(-2.6, -4.3), (2.6, -4.3)], soil, 0.06)
    bank([(x, y - 0.12) for x, y in bot] + [(-2.6, -4.3), (2.6, -4.3)], grass, 0.12) if False else None
    bank([(x, y - 0.3) for x, y in bot] + [(-2.6, -4.3), (2.6, -4.3)], grass, 0.1)
    # top bank
    tb = wavy(-2.6, 2.6, 3.45, 0.1, 14); bank(tb + [(2.6, 4.3), (-2.6, 4.3)], soil, 0.06); bank([(x, y + 0.25) for x, y in tb] + [(2.6, 4.3), (-2.6, 4.3)], grass, 0.1)
    # side banks (thin)
    for sx in (-1, 1):
        sd = [(sx * (2.08 + 0.06 * math.sin(i)), -2.9 + i * 0.5) for i in range(14)]
        bank(sd + [(sx * 2.6, 3.6), (sx * 2.6, -2.9)], grass, 0.1)
    # reeds in clumps on the banks
    reed = noise_mat('reed', '#5e8e3e', '#76a64a', 6, 0.8, 0.2); head = mat('cat', '#8a5a34', 0.8)
    for cx, cy in ((-1.9, 3.4), (-1.5, 3.6), (1.7, 3.5), (2.0, -2.0), (-2.0, -1.2), (2.0, 1.6), (-2.05, 0.9), (1.4, -2.95)):
        for k in range(7):
            ox, oy = cx + rnd.uniform(-.18, .18), cy + rnd.uniform(-.18, .18)
            blade((ox, oy), rnd.uniform(.7, 1.1), (rnd.uniform(-.35, .35), rnd.uniform(-.35, .35)), reed)
    # lily pads (only four, big)
    pad = noise_mat('pad', '#4e8e3e', '#5ea04a', 5, 0.6, 0.2)
    for px_, py_, r, a in ((-1.2, 2.3, 0.34, 0.4), (1.3, 0.4, 0.3, 2.2), (-1.4, -0.9, 0.28, 4.0), (0.6, 2.9, 0.24, 1.0)):
        o = cyl((px_, py_, 0.02), r, 0.02, pad, 48)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(px_ + math.cos(a) * r * 0.6, py_ + math.sin(a) * r * 0.6, 0.02)); cut = bpy.context.object
        cut.scale = (r * 1.2, 0.03, 0.2); cut.rotation_euler.z = a; cut.hide_render = True
        bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    flw = mat('lotus', '#f6b8c8', 0.6, 0.1, sss=0.2)
    for k in range(6):
        a = k * math.tau / 6; sphere((-1.2 + math.cos(a) * 0.07, 2.3 + math.sin(a) * 0.07, 0.07), (0.09, 0.05, 0.04), flw, 16, rot=(0, 0, a))
    sphere((-1.2, 2.3, 0.09), (0.04, 0.04, 0.03), mat('lc', '#f6d860', 0.6), 16)
    # straw nest on the bottom bank
    straw = noise_mat('straw', '#c8a058', '#e0bc70', 18, 0.9, 0.8, .3, .7, 8)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.46, minor_radius=0.16, major_segments=64, minor_segments=24, location=(0, -3.3, 0.18)); o = bpy.context.object
    o.scale = (1, 0.82, 0.8); smooth(o); o.data.materials.append(straw)
    tx = bpy.data.textures.new('nestd', 'CLOUDS'); tx.noise_scale = 0.08; d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.04
    cyl((0, -3.3, 0.14), 0.36, 0.06, noise_mat('nestin', '#9a7a42', '#b08c50', 20, 0.9, 0.6), 32)
    render(sc, 'bg')
    META['nest'] = tp(0, -3.3); META['water'] = [tp(-2.0, 3.2), tp(2.0, -2.6)]
    META['pads'] = [tp(-1.2, 2.3) + [54], tp(1.3, 0.4) + [48], tp(-1.4, -0.9) + [45], tp(0.6, 2.9) + [38]]

def duck(name, mother, pose):
    sc = reset(True); light(sc); top(sc, 120 if mother else 72, 120 if mother else 72)
    s = 1.0 if mother else 0.55
    if mother:
        body = noise_mat('mb', '#8a6a4a', '#9c7a56', 14, 0.8, 0.1); headm = mat('mh', '#2e7a4a', 0.5, 0.3); bill = mat('bill', '#f0b030', 0.5)
        wing = mat('mw', '#6a5038', 0.7); speck = mat('spec', '#3a5aa8', 0.4, 0.3); ring = mat('ring', '#f4f2ea', 0.6)
    else:
        body = mat('db', '#f2c43a', 0.85, 0.1); headm = mat('dh', '#f4cc44', 0.85, 0.1); bill = mat('dbill', '#f09a30', 0.5); wing = mat('dw', '#e0ac2a', 0.85); speck = wing; ring = body
    eye = mat('eye', '#1a1210', 0.4, 0.2)
    # facing +y (up in the frame); the game rotates the sprite to the heading
    sphere((0, -0.03 * s, 0.1 * s), (0.17 * s, 0.26 * s, 0.12 * s), body, 40)
    sphere((0, -0.27 * s, 0.13 * s), (0.07 * s, 0.07 * s, 0.05 * s), body, 24)            # tail
    for sx in (-1, 1):
        o = sphere((sx * 0.1 * s, -0.04 * s, 0.17 * s), (0.08 * s, 0.19 * s, 0.05 * s), wing, 32); o.rotation_euler = (0, sx * 0.25, sx * -0.08)
        if mother: sphere((sx * 0.13 * s, -0.12 * s, 0.19 * s), (0.03 * s, 0.05 * s, 0.02 * s), speck, 16)
    if mother: cyl((0, 0.16 * s, 0.17 * s), 0.07 * s, 0.03 * s, ring, 24)
    sphere((0, 0.22 * s, 0.22 * s), (0.1 * s, 0.11 * s, 0.09 * s), headm, 32)
    sphere((0, 0.35 * s, 0.21 * s), (0.045 * s, 0.07 * s, 0.022 * s), bill, 24)
    for sx in (-1, 1): sphere((sx * 0.075 * s, 0.25 * s, 0.26 * s), (0.017 * s, 0.017 * s, 0.017 * s), eye, 12)
    # paddling feet peeking out behind, alternating
    foot = mat('foot', '#f09a30', 0.6)
    for sx in (-1, 1):
        dy = (0.04 if (pose == 0) == (sx < 0) else -0.04) * s
        o = sphere((sx * 0.09 * s, -0.24 * s + dy, 0.02), (0.05 * s, 0.05 * s, 0.01), foot, 16)
    render(sc, name)

def build_log(name, L):
    sc = reset(True); light(sc); top(sc, int(L * PX + 30), int(L * PX + 30))
    bark = noise_mat('bark', '#7a5a3a', '#8e6a44', 12, 0.9, 0.6)
    cyl((0, 0, 0.1), 0.12, L, bark, 24, rot=(0, math.radians(90), 0))
    end = mat('end', '#d8b47e', 0.8)
    for sx in (-1, 1): cyl((sx * L / 2, 0, 0.1), 0.11, 0.01, end, 24, rot=(0, math.radians(90), 0))
    o = cyl((0.15 * L, 0.0, 0.2), 0.03, 0.18, bark, 12, rot=(math.radians(60), 0, 0.5))
    sphere((-0.2 * L, 0.02, 0.2), (0.08, 0.05, 0.03), mat('leaf', '#6aa04a', 0.6), 16)
    render(sc, name)

JOBS = {'bg': build_bg, 'mom0': lambda: duck('mom0', True, 0), 'mom1': lambda: duck('mom1', True, 1),
        'chick0': lambda: duck('chick0', False, 0), 'chick1': lambda: duck('chick1', False, 1),
        'log_s': lambda: build_log('log_s', 1.2), 'log_l': lambda: build_log('log_l', 1.9)}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
