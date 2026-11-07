# Renders the layers for hanetsuki.html, seen from the front: a New Year garden (winter sky, plaster wall, kadomatsu,
# a plum branch, snow) and sprites: the hagoita paddle, the shuttlecock and three floating lucky targets.
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




def front_cam(sc, scale, rx, ry, tz=0.0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, -30, tz)); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = rx, ry

def front_light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, -10, 10)); s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(25); s.data.color = srgb('#fff2e0')
    s.rotation_euler = (math.radians(55), 0, math.radians(-25))
    bpy.ops.object.light_add(type='AREA', location=(3, -8, 2)); a = bpy.context.object; a.data.energy = 600; a.data.size = 8; a.data.color = srgb('#e8f0ff')
    a.rotation_euler = (Vector((0, 0, 0)) - a.location).to_track_quat('-Z', 'Y').to_euler()

def F(px, py): return ((px - 360) / 160, (640 - py) / 160)

def build_bg():
    sc = reset(False); front_light(sc); front_cam(sc, 8.0, 720, 1280)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe6fa'), 1)
    # winter sky backdrop with a faint gradient, snowy ground, a plaster wall with a tile cap, pine and plum
    sky = bpy.data.materials.new('sky'); sky.use_nodes = True; nt = sky.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); se = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], se.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#f6efe0'), 1); r.color_ramp.elements[1].color = (*srgb('#a8d4f2'), 1)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = -0.5; mr.inputs[2].default_value = 0.5; nt.links.new(se.outputs['Y'], mr.inputs[0]); nt.links.new(mr.outputs[0], r.inputs['Fac'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(r.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5, 0)); o = bpy.context.object; o.scale = (6, 9, 1); o.rotation_euler = (math.radians(90), 0, 0); o.data.materials.append(sky)
    gx, gz = F(360, 1090)
    snow = noise_mat('snow', '#f6f8fa', '#e6eef4', 6, 0.8, 0.3)
    box((0, 0, gz - 1.5), (8, 3, 3.0), snow, 0.05)
    plaster = noise_mat('plaster', '#f4eee2', '#e8e0d0', 6, 0.95, 0.1)
    wx, wz = F(360, 900)
    box((0, 2.5, wz + 0.6), (8, 0.3, 1.2 + 1.2), plaster, 0.02)
    tile = mat('tile', '#4a5058', 0.6, 0.2)
    box((0, 2.3, wz + 1.85), (8.2, 0.7, 0.14), tile, 0.04)
    for i in range(-18, 19): cyl((i * 0.23, 2.0, wz + 1.88), 0.07, 0.5, tile, 16, rot=(math.radians(90), 0, 0))
    # kadomatsu at both sides: three slanted bamboo, pine sprigs, a straw base
    bam = noise_mat('bam', '#7aa84a', '#94bc5a', 20, 0.4, 0.1); straw = noise_mat('straw', '#d8b868', '#c8a050', 40, 0.9, 0.5)
    pine = noise_mat('pine', '#2e5a2e', '#3e6e3a', 30, 0.9, 0.6); rope = mat('rope', '#c8a050', 0.9)
    for sx in (-1, 1):
        bx = sx * 1.95
        cyl((bx, 0.5, gz + 0.25), 0.34, 0.5, straw, 48)
        for k, (dx, h) in enumerate(((-0.12, 1.3), (0.0, 1.6), (0.12, 1.15))):
            o = cyl((bx + dx, 0.45, gz + 0.5 + h / 2), 0.07, h, bam, 24)
            cyl((bx + dx, 0.45, gz + 0.5 + h), 0.071, 0.01, mat('cut', '#e8e0b0', 0.6), 24).rotation_euler = (math.radians(30), 0, 0)
        for k in range(9): sphere((bx + random.Random(k + sx).uniform(-.35, .35), 0.3, gz + 0.55 + random.Random(k * 7 + sx).uniform(0, .35)), (0.14, 0.1, 0.09), pine, 16)
        cyl((bx, 0.5, gz + 0.35), 0.345, 0.06, rope, 48)
    # a plum branch leaning over the wall
    br = mat('branch', '#4a3428', 0.8); pl = mat('plum', '#f2a0b8', 0.7); pc = mat('plumc', '#e8708e', 0.7)
    px, pz = F(600, 840)
    pts = [(px + 0.8, pz - 0.3), (px + 0.2, pz + 0.2), (px - 0.4, pz + 0.35), (px - 0.9, pz + 0.7)]
    for (a, b2) in zip(pts, pts[1:]):
        L = math.hypot(b2[0] - a[0], b2[1] - a[1]); o = cyl(((a[0] + b2[0]) / 2, 1.8, (a[1] + b2[1]) / 2), 0.04, L, br, 12); o.rotation_euler = (0, math.atan2(b2[0] - a[0], b2[1] - a[1]), 0)
    rnd = random.Random(9)
    for i in range(10):
        t = rnd.uniform(0, 1); k = min(2, int(t * 3)); a, b2 = pts[k], pts[k + 1]; u = t * 3 - k
        cx, cz = a[0] + (b2[0] - a[0]) * u + rnd.uniform(-.08, .08), a[1] + (b2[1] - a[1]) * u + rnd.uniform(-.06, .1)
        for j in range(5):
            an = j * 2 * math.pi / 5; sphere((cx + 0.045 * math.cos(an), 1.7, cz + 0.045 * math.sin(an)), (0.04, 0.01, 0.04), pl, 12)
        sphere((cx, 1.68, cz), (0.018, 0.01, 0.018), pc, 8)
    render(sc, 'bg')

def build_paddle():
    sc = reset(True); front_light(sc); front_cam(sc, 1.6, 256, 256)
    wd = wood('kiri', '#e8d2a8', '#dcc496')
    # hagoita: a flat rounded board with a handle, the face painted with a red plum on gold
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.32, depth=0.05, location=(0, 0, 0.18), rotation=(math.radians(90), 0, 0)); o = bpy.context.object
    o.scale = (1, 1.45, 1); bevel(o, 0.015, 3); smooth(o); o.data.materials.append(wd)
    box((0, 0, -0.42), (0.13, 0.04, 0.42), wd, 0.015)
    gold = mat('gold', '#e8b84a', 0.4, 0.4); red = mat('red', '#d8483a', 0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.26, depth=0.01, location=(0, -0.03, 0.2), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (1, 1.4, 1); o.data.materials.append(gold)
    for j in range(5):
        an = j * 2 * math.pi / 5 + math.pi / 2; sphere((0.09 * math.cos(an), -0.04, 0.2 + 0.09 * math.sin(an)), (0.08, 0.01, 0.08), red, 24)
    sphere((0, -0.05, 0.2), (0.04, 0.01, 0.04), mat('yel', '#f6e070', 0.6), 16)
    render(sc, 'paddle')

def build_hane():
    sc = reset(True); front_light(sc); front_cam(sc, 0.7, 112, 112)
    sphere((0, 0, -0.12), (0.07, 0.07, 0.07), mat('mukuro', '#1e1a18', 0.4, 0.3), 32)
    cols = ['#e8483a', '#f6d040', '#4aa86a', '#4a8ae0']
    for k in range(4):
        an = (k - 1.5) * 0.35
        o = sphere((math.sin(an) * 0.1, (k % 2) * 0.01, -0.02 + math.cos(an) * 0.1), (0.05, 0.01, 0.13), mat('f%d' % k, cols[k], 0.6), 24); o.rotation_euler = (0, an, 0)
    render(sc, 'hane')

def build_target(name):
    sc = reset(True); front_light(sc); front_cam(sc, 1.2, 160, 160)
    if name == 'daruma':
        red = mat('dr', '#d8382a', 0.5, 0.2); wh = mat('dw', '#f6f0e4', 0.6); blk = mat('blk', '#1e1410', 0.6, 0.05); gold = mat('dg', '#e8b84a', 0.4, 0.4)
        sphere((0, 0, 0), (0.36, 0.3, 0.4), red, 48)
        paint_on((0, 0, 0), (0.36, 0.3, 0.4), wh, (0, -0.3, 0.08), (0.22, 0.2, 0.17))
        for sx in (-1, 1): sphere((sx * 0.09, -0.3, 0.1), (0.04, 0.01, 0.04), blk, 16)
        paint_on((0, 0, 0), (0.36, 0.3, 0.4), gold, (0, -0.3, -0.24), (0.14, 0.2, 0.08))
    elif name == 'koma':
        cols = ['#d8483a', '#f6d040', '#4a8ae0', '#4aa86a', '#d8483a']
        for k, c in enumerate(cols):
            r = 0.36 - k * 0.07
            cyl((0, 0, 0.02 + k * 0.012), r, 0.08, mat('kc%d' % k, c, 0.5, 0.2), 48)
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.36, depth=0.3, location=(0, 0, -0.17), rotation=(math.radians(180), 0, 0)); o = bpy.context.object; smooth(o); o.data.materials.append(wood('kw', '#c89a62', '#b88a52'))
        cyl((0, 0, 0.18), 0.04, 0.24, mat('kax', '#6a4a2a', 0.6), 16)
        for o in bpy.context.scene.objects:
            if o.type == 'MESH': o.rotation_euler.x += math.radians(-18)
    else:  # mikan on a little kagami mochi
        mochi = mat('mo', '#fbf8f0', 0.7); mk = noise_mat('mk', '#f29a2a', '#f6b040', 30, 0.6, 0.3); lf = mat('lf', '#4a8a3a', 0.6)
        sphere((0, 0, -0.22), (0.34, 0.3, 0.13), mochi, 48); sphere((0, 0, -0.04), (0.26, 0.24, 0.11), mochi, 48)
        sphere((0, 0, 0.14), (0.15, 0.15, 0.13), mk, 32); sphere((0.08, -0.02, 0.27), (0.08, 0.02, 0.035), lf, 16, rot=(0, 0.5, 0))
    render(sc, name)

JOBS = {'bg': build_bg, 'paddle': build_paddle, 'hane': build_hane, 'daruma': lambda: build_target('daruma'), 'koma': lambda: build_target('koma'), 'kagami': lambda: build_target('kagami')}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
