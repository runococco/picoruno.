# Renders the layers for sasabune.html, all from straight above: a looping river tile (grass banks, bank stones, riverbed
# pebbles, water), the bamboo-leaf boat with its frog passenger, rocks, a drifting log, sakura, ginkgo leaf, whirlpool, bridge.
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




L = 8.0      # loop period of the river tile in world units (1280 px)
RX = 1.5625  # river half width (px 110..610)

def rect_cam(sc, w, h, scale):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, 0, 30)); c = bpy.context.object; c.rotation_euler = (0, 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = w, h

def periodic(y):
    return [yy for yy in (y - L, y, y + L) if -5.6 < yy < 5.6]

def flat_stone(loc, s, m, rot=0, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, location=loc); o = bpy.context.object
    o.scale = s; o.rotation_euler = (0, 0, rot); smooth(o); o.data.materials.append(m); return o

def build_bg():
    sc = reset(False); rect_cam(sc, 720, 1600, 10.0)
    rnd = random.Random(7)
    grass = noise_mat('grass', '#6aa84a', '#86c05a', 9, 0.9, 0.5, .3, .72)
    bed = noise_mat('bed', '#5cb4cc', '#7cc8da', 5, 0.6, 0.3, .3, .75)
    for sx in (-1, 1):
        o = box((sx * (RX + 1.5 + 0.02), 0, -0.05), (3.0, 14, 0.2), grass, 0.06)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.32)); o = bpy.context.object; o.scale = (2 * RX + 0.4, 14, 1); o.data.materials.append(bed)
    # pebbles on the riverbed
    pm = [noise_mat('peb%d' % i, c1, c2, 20, 0.8, 0.2) for i, (c1, c2) in enumerate([('#4c98ae', '#5aa6ba'), ('#6aa8a8', '#78b6b2'), ('#4a8ca8', '#5a9cb6'), ('#84bcc0', '#94c8ca')])]
    for i in range(130):
        x = rnd.uniform(-RX + .05, RX - .05); y = rnd.uniform(-4, 4); r = rnd.uniform(.04, .13)
        for yy in periodic(y): flat_stone((x, yy, -0.31), (r, r * rnd.uniform(.6, 1), r * .4), pm[i % 4], rnd.uniform(0, 3))
        rnd.random()
    # stones along both banks
    sm = [noise_mat('bs%d' % i, c1, c2, 12, 0.85, 0.35) for i, (c1, c2) in enumerate([('#9a968c', '#b4b0a4'), ('#86888a', '#a2a4a6'), ('#a89c88', '#c0b6a2')])]
    for sx in (-1, 1):
        y = -4.0
        while y < 4.0:
            r = rnd.uniform(.13, .24); x = sx * (RX + rnd.uniform(-.06, .08))
            for yy in periodic(y): flat_stone((x, yy, -0.1), (r * 1.15, r, r * .55), sm[rnd.randrange(3)], rnd.uniform(0, 3))
            y += r * rnd.uniform(1.3, 1.9)
    # clover clumps and small flowers on the grass
    dg = mat('clump', '#4e8c3a', 0.85); fl = [mat('fw', '#fbfaf2', .7), mat('fy', '#f6d23e', .7), mat('fp', '#f4a6c0', .7)]
    for i in range(70):
        sx = rnd.choice((-1, 1)); x = sx * rnd.uniform(RX + .35, 2.4); y = rnd.uniform(-4, 4)
        for yy in periodic(y):
            for k in range(4):
                a = k * 1.6 + i; sphere((x + .07 * math.cos(a), yy + .07 * math.sin(a), 0.06), (.09, .07, .04), dg, 16, (0, 0, a))
        if i % 2 == 0:
            m = fl[i % 3]; fx, fy = x + rnd.uniform(-.25, .25), y + rnd.uniform(-.25, .25)
            for yy in periodic(fy):
                for k in range(5):
                    a = k * 2 * math.pi / 5; sphere((fx + .04 * math.cos(a), yy + .04 * math.sin(a), 0.1), (.035, .035, .015), m, 12)
                sphere((fx, yy, 0.11), (.02, .02, .012), fl[1] if m != fl[1] else mat('fo', '#e88a3a', .7), 12)
    # water sheet with a gentle ripple
    wm = bpy.data.materials.new('water'); wm.use_nodes = True; nt = wm.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#bfe8f4'), 1); b.inputs['Roughness'].default_value = 0.15; b.inputs['Alpha'].default_value = 0.12
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.13)); o = bpy.context.object; o.scale = (2 * RX + 0.3, 14, 1); o.data.materials.append(wm); o.visible_diffuse = False
    render(sc, 'bg_raw')
    META['river'] = [110, 610]

def leaf_mat(name, c1, c2):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); se = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], se.inputs[0])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(se.outputs['X'], ab.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.0; r.color_ramp.elements[0].color = (*srgb(c2), 1)
    r.color_ramp.elements[1].position = 0.012; r.color_ramp.elements[1].color = (*srgb(c1), 1)
    nt.links.new(ab.outputs[0], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5; b.inputs['Specular IOR Level'].default_value = .2
    return m

def build_boat():
    sc = reset(True); top_cam(sc, 1.3, 240)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.001], context='VERTS')
    for v in bm.verts:
        x, y, z = v.co; t = math.sqrt(max(0, 1 - y * y))
        v.co = Vector((x * 0.17 * t, y * 0.58, z * 0.09 * t + 0.1 * y ** 4))
    bm.to_mesh(o.data); bm.free(); smooth(o)
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.012
    o.data.materials.append(leaf_mat('leaf', '#4f9a3c', '#a6d27a'))
    # the folded tips of the leaf boat
    tipm = mat('tip', '#3f8430', 0.55)
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.05, depth=0.2, location=(0, sy * 0.43, 0.08), rotation=(math.radians(-90 * sy), 0, 0))
        t = bpy.context.object; t.scale = (1, 0.35, 1); smooth(t); t.data.materials.append(tipm)
    # a little frog passenger: body, two eye bumps with solid black dots
    fg = mat('frog', '#8cc84e', 0.6); blk = mat('blk', '#1a1410', 0.9, 0.0)
    sphere((0, -0.05, -0.02), (0.1, 0.12, 0.07), fg, 32)
    for sx in (-1, 1):
        sphere((sx * 0.055, 0.04, 0.03), (0.04, 0.04, 0.035), fg, 24)
        sphere((sx * 0.058, 0.05, 0.062), (0.017, 0.017, 0.008), blk, 16)
        sphere((sx * 0.1, -0.1, -0.01), (0.04, 0.03, 0.02), fg, 16)
    render(sc, 'boat')

def build_rock(name, seed, sx, sy):
    sc = reset(True); top_cam(sc, 1.2, 200)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, location=(0, 0, 0)); o = bpy.context.object
    tx = bpy.data.textures.new('rt' + name, 'CLOUDS'); tx.noise_scale = 0.45
    random.seed(seed); o.location = (0, 0, 0)
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.42; d.texture_coords = 'GLOBAL'
    bpy.context.view_layer.update()
    o.scale = (sx, sy, 0.26); o.rotation_euler = (0, 0, seed); smooth(o)
    tc_ = bpy.data.objects.new('off', None); bpy.context.collection.objects.link(tc_); tc_.location = (seed * 3.1, seed * 1.7, 0)
    d.texture_coords = 'OBJECT'; d.texture_coords_object = tc_
    o.data.materials.append(noise_mat('rock' + name, '#7e7c76', '#a8a59c', 7, 0.8, 0.6, .3, .75))
    # moss on top
    m2 = noise_mat('moss' + name, '#5c8a3a', '#7aa648', 10, 0.9, 0.3)
    render(sc, name)

def build_log():
    sc = reset(True); top_cam(sc, 2.6, 400)
    bark = noise_mat('bark', '#6e4a2c', '#8a6038', 16, 0.9, 0.8, .3, .7)
    o = cyl((0, 0, 0), 0.14, 2.2, bark, 32, rot=(0, math.radians(90), 0))
    end = wood('endw', '#d8b07a', '#b88a56')
    for sx in (-1, 1): cyl((sx * 1.1, 0, 0), 0.128, 0.02, end, 32, rot=(0, math.radians(90), 0))
    cyl((0.4, 0.13, 0.02), 0.04, 0.22, bark, 16, rot=(math.radians(70), 0, 0.3))
    render(sc, 'log')

def build_sakura():
    sc = reset(True); top_cam(sc, 0.36, 96)
    pk = mat('sak', '#f7b8cc', 0.6); ce = mat('sakc', '#e8708e', 0.6)
    for k in range(5):
        a = k * 2 * math.pi / 5 + math.pi / 2
        p = sphere((0.075 * math.cos(a), 0.075 * math.sin(a), 0), (0.075, 0.055, 0.012), pk, 24, (0, 0, a))
    sphere((0, 0, 0.01), (0.03, 0.03, 0.01), ce, 16)
    render(sc, 'sakura')

def build_icho():
    sc = reset(True); top_cam(sc, 0.5, 120)
    bm = bmesh.new(); n = 24; R = 0.2
    c = bm.verts.new((0, -0.12, 0)); vs = []
    for i in range(n + 1):
        a = math.radians(90 - 60 + 120 * i / n); rr = R * (1 - 0.18 * math.exp(-((i - n / 2) ** 2) / 3))
        vs.append(bm.verts.new((rr * math.cos(a), -0.12 + rr * math.sin(a), 0.02 * math.sin(math.pi * i / n))))
    for i in range(n): bm.faces.new((c, vs[i], vs[i + 1]))
    me = bpy.data.meshes.new('icho'); bm.to_mesh(me); o = bpy.data.objects.new('icho', me); bpy.context.collection.objects.link(o)
    o.modifiers.new('s', 'SOLIDIFY').thickness = 0.01
    o.data.materials.append(mat('ichom', '#f2c230', 0.55))
    cyl((0, -0.17, 0), 0.008, 0.12, mat('stem', '#c89a28', 0.6), 8, rot=(math.radians(90), 0, 0))
    render(sc, 'icho')

def build_uzu():
    sc = reset(True); top_cam(sc, 1.6, 300)
    m = bpy.data.materials.new('uzu'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); se = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], se.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'; nt.links.new(se.outputs['Y'], at.inputs[0]); nt.links.new(se.outputs['X'], at.inputs[1])
    fl = nt.nodes.new('ShaderNodeVectorMath'); fl.operation = 'MULTIPLY'; fl.inputs[1].default_value = (1, 1, 0); nt.links.new(tc.outputs['Object'], fl.inputs[0])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(fl.outputs[0], ln.inputs[0])
    a1 = nt.nodes.new('ShaderNodeMath'); a1.operation = 'MULTIPLY'; a1.inputs[1].default_value = 3 / (2 * math.pi); nt.links.new(at.outputs[0], a1.inputs[0])
    sq = nt.nodes.new('ShaderNodeMath'); sq.operation = 'SQRT'; nt.links.new(ln.outputs['Value'], sq.inputs[0])
    l1 = nt.nodes.new('ShaderNodeMath'); l1.operation = 'MULTIPLY'; l1.inputs[1].default_value = 7; nt.links.new(sq.outputs[0], l1.inputs[0])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(a1.outputs[0], ad.inputs[0]); nt.links.new(l1.outputs[0], ad.inputs[1])
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; nt.links.new(ad.outputs[0], fr.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); e = r.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*srgb('#2a6e9e'), 1); e[1].position = 0.55; e[1].color = (*srgb('#cfeeff'), 1)
    e2 = r.color_ramp.elements.new(0.75); e2.color = (*srgb('#5aa6d6'), 1)
    nt.links.new(fr.outputs[0], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    # fade to transparent at the rim
    fa = nt.nodes.new('ShaderNodeMapRange'); fa.inputs[1].default_value = 0.45; fa.inputs[2].default_value = 0.78
    fa.inputs[3].default_value = 0.85; fa.inputs[4].default_value = 0.0; nt.links.new(ln.outputs['Value'], fa.inputs[0])
    nt.links.new(fa.outputs[0], b.inputs['Alpha']); b.inputs['Roughness'].default_value = 0.3
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, location=(0, 0, 0)); o = bpy.context.object
    o.scale = (0.8, 0.8, 0.12)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.001], context='VERTS'); bm.to_mesh(o.data); bm.free()
    smooth(o); o.data.materials.append(m)
    render(sc, 'uzu')

def build_bridge():
    sc = reset(True); rect_cam(sc, 720, 240, 4.5)
    pl = planks(); post = wood('post', '#8a5a34', '#9c6a3e'); rail = mat('rail', '#a06a3c', 0.7)
    rnd = random.Random(3); x = -2.3
    while x < 2.3:
        w = rnd.uniform(.17, .22); box((x + w / 2, rnd.uniform(-.02, .02), 0), (w - .02, .62, .06), pl, .01); x += w
    for sy in (-1, 1):
        box((0, sy * .3, .22), (4.6, .06, .05), rail, .015)
        for px in (-1.75, -0.6, 0.6, 1.75): cyl((px, sy * .3, .1), .05, .3, post, 16)
    render(sc, 'bridge')

JOBS = {'bg': build_bg, 'boat': build_boat, 'rock1': lambda: build_rock('rock1', 1, .42, .36), 'rock2': lambda: build_rock('rock2', 2, .5, .3),
        'rock3': lambda: build_rock('rock3', 3, .34, .32), 'log': build_log, 'sakura': build_sakura, 'icho': build_icho, 'uzu': build_uzu, 'bridge': build_bridge}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
