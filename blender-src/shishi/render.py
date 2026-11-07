# Renders the layers for shishi.html: a garden behind a plaster wall seen slightly from above (background with three
# shishi-odoshi stands, striking stones and basins, a koi pond), plus the bamboo tube, the water pipe, a heron (two wing poses) and koi.
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




E = math.radians(20); TGT = Vector((0, 0, 1.3)); LANES = [-1.5, -0.25, 1.0]   # tilted garden camera; lane pivots in world x
PIV_Z = 0.55; TL = 1.4; PF = 0.4; REST = math.radians(28)

def gproj(x, y, z):
    v = (y - TGT.y) * math.sin(E) + (z - TGT.z) * math.cos(E)
    return [round(360 + (x - TGT.x) * 160, 1), round(640 - v * 160, 1)]

def garden_cam(sc):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    d = Vector((0, math.cos(E), -math.sin(E))); loc = TGT - d * 30
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = 8.0; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280

def front_cam(sc, scale, rx, ry):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, -30, 0)); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = rx, ry

def front_light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, -10, 10)); s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(25); s.data.color = srgb('#fff2e0')
    s.rotation_euler = (math.radians(55), 0, math.radians(-25))
    bpy.ops.object.light_add(type='AREA', location=(3, -8, 2)); a = bpy.context.object; a.data.energy = 600; a.data.size = 8; a.data.color = srgb('#e8f0ff')
    a.rotation_euler = (Vector((0, 0, 0)) - a.location).to_track_quat('-Z', 'Y').to_euler()

def rock(loc, s, m, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, location=loc); o = bpy.context.object
    tx = bpy.data.textures.new('rk%d' % seed, 'CLOUDS'); tx.noise_scale = 0.5
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.25
    e = bpy.data.objects.new('off%d' % seed, None); bpy.context.collection.objects.link(e); e.location = (seed * 2.3, seed * 1.1, 0); d.texture_coords = 'OBJECT'; d.texture_coords_object = e
    o.scale = s; smooth(o); o.data.materials.append(m); return o

def build_bg():
    sc = reset(False); front_light(sc); garden_cam(sc)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#bfe0f6'), 1)
    moss = noise_mat('moss', '#6a9a4a', '#84b05a', 12, 0.95, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -3.5, 0)); o = bpy.context.object; o.scale = (10, 13, 1); o.data.materials.append(moss)
    # back wall: white plaster on a stone footing, dark tile cap
    plaster = noise_mat('plaster', '#f2ece0', '#e6dfd0', 6, 0.95, 0.1)
    box((0, 3.2, 1.0), (10, 0.3, 2.0), plaster, 0.02)
    box((0, 3.0, 0.15), (10, 0.36, 0.3), noise_mat('foot', '#8a8a84', '#a2a29a', 10, 0.9, 0.4), 0.03)
    tile = mat('tile', '#4a5058', 0.6, 0.2)
    box((0, 3.1, 2.08), (10.2, 0.7, 0.16), tile, 0.04)
    for i in range(-22, 23): cyl((i * 0.23, 2.8, 2.1), 0.07, 0.5, tile, 16, rot=(math.radians(90), 0, 0))
    # pond: dark water sheet sunk into the moss, edged with stones
    wm = bpy.data.materials.new('pond'); wm.use_nodes = True; nt = wm.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#2a6a7a'), 1); b.inputs['Roughness'].default_value = 0.12
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4.6, 0.01)); o = bpy.context.object; o.scale = (9.0, 7.4, 1); o.data.materials.append(wm)
    rnd = random.Random(4); stn = [noise_mat('ps%d' % i, c1, c2, 9, 0.85, 0.4) for i, (c1, c2) in enumerate([('#8e8c86', '#a8a69e'), ('#7e8288', '#9aa0a4'), ('#a09886', '#b6ae9c')])]
    x = -4.6
    while x < 4.6:
        r = rnd.uniform(.22, .38); rock((x + r, -0.9, 0.05), (r, r * .8, r * .6), stn[rnd.randrange(3)], int(x * 10) + 50); x += r * rnd.uniform(1.7, 2.1)
    # shishi-odoshi bases: two posts and an axle per lane, a striking stone and a stone basin
    post = wood('post', '#8a6a44', '#9c7a50'); basin = noise_mat('basin', '#8c8a84', '#a4a29a', 8, 0.85, 0.4)
    wtr = mat('bw', '#3a7a8a', 0.1)
    for i, lx in enumerate(LANES):
        for sy in (0.12,):
            box((lx, sy + 0.05, PIV_Z / 2 + 0.05), (0.07, 0.07, PIV_Z + 0.1), post, 0.01)
        cl = Vector((lx - TL * PF * math.cos(REST), 0, PIV_Z - TL * PF * math.sin(REST)))
        rock((cl.x, 0.0, cl.z / 2 - 0.02), (0.16, 0.16, max(0.12, cl.z / 2)), stn[i % 3], 90 + i)
        ox = lx + TL * (1 - PF) * math.cos(math.radians(25)) + 0.05
        cyl((ox, 0.0, 0.12), 0.3, 0.24, basin, 32); cyl((ox, 0.0, 0.245), 0.24, 0.01, wtr, 32)
        for k in range(5): rock((lx + rnd.uniform(-.6, .9), rnd.uniform(.4, 1.6), 0.03), (rnd.uniform(.08, .16),) * 2 + (.07,), stn[k % 3], 200 + i * 10 + k)
    # a few shrubs along the wall
    leaf = noise_mat('shrub', '#3e7a3a', '#5a9448', 8, 0.9, 0.6)
    for sx in (-3.2, -2.1, 2.3, 3.3, 0.6):
        for k in range(3): sphere((sx + k * .3 - .3, 2.6, 0.45 + (k % 2) * .15), (0.42, 0.35, 0.4), leaf, 24)
    render(sc, 'bg')
    META['lanes'] = [gproj(lx, 0, PIV_Z) for lx in LANES]
    META['pond'] = [gproj(0, -0.9, 0)[1], gproj(0, -8, 0)[1]]
    META['wall'] = gproj(0, 3.2, 2.0)[1]

def bamboo_mat(name, c1, c2):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.3, 6, 6); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.35
    return m

def build_tube():
    sc = reset(True); front_light(sc); front_cam(sc, 1.8, 256, 256)
    m = bamboo_mat('tube', '#a8b858', '#c4cc6a'); node = mat('node', '#8a9a48', 0.4)
    # pivot at the origin; closed end to the left (-x), open end to the right (+x)
    x0, x1 = -TL * PF, TL * (1 - PF)
    cyl(((x0 + x1) / 2, 0, 0), 0.1, TL, m, 32, rot=(0, math.radians(90), 0))
    for nx in (x0 + 0.02, 0.3): cyl((nx, 0, 0), 0.108, 0.04, node, 32, rot=(0, math.radians(90), 0))
    cyl((x1 + 0.005, 0, 0), 0.075, 0.01, mat('hole', '#3a3020', 0.9), 32, rot=(0, math.radians(90), 0))
    cyl((0, -0.12, 0), 0.03, 0.06, mat('axle', '#6a4a2a', 0.7), 16, rot=(math.radians(90), 0, 0))
    render(sc, 'tube')

def build_kakei():
    sc = reset(True); front_light(sc); front_cam(sc, 6.25, 1000, 160)
    m = bamboo_mat('kakei', '#9aac52', '#b8c262'); node = mat('node2', '#7e8e42', 0.4)
    cyl((-0.1, 0, 0.1), 0.07, 6.0, m, 24, rot=(0, math.radians(90), 0))
    for k in range(6): cyl((-2.9 + k * 1.0, 0, 0.1), 0.076, 0.03, node, 24, rot=(0, math.radians(90), 0))
    o = cyl((2.95, 0, -0.03), 0.06, 0.28, m, 24, rot=(0, math.radians(35), 0))
    render(sc, 'kakei')

def build_heron(name, up):
    sc = reset(True); front_light(sc); front_cam(sc, 1.8, 256, 256)
    w = mat('wh', '#f6f4ee', 0.7); yb = mat('bk', '#f2c43a', 0.5); blk = mat('blk', '#1e1410', 0.6, 0.05); leg = mat('leg', '#4a4038', 0.7)
    sphere((0, 0, 0), (0.32, 0.14, 0.15), w, 40)                                  # body, flying to the left
    sphere((-0.34, 0, 0.12), (0.14, 0.06, 0.06), w, 24, rot=(0, math.radians(30), 0))
    sphere((-0.48, 0, 0.2), (0.08, 0.07, 0.07), w, 24)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.03, depth=0.2, location=(-0.62, 0, 0.19)); o = bpy.context.object; o.rotation_euler = (0, math.radians(-90), 0); o.data.materials.append(yb)
    sphere((-0.5, -0.06, 0.23), (0.018, 0.012, 0.018), blk, 12)
    for sx in (0.35, 0.42): cyl((sx, 0, -0.03), 0.012, 0.36, leg, 8, rot=(0, math.radians(80), 0))
    ang = math.radians(55 if up else -35)
    o = sphere((0.02, -0.02, 0.06), (0.24, 0.05, 0.11), w, 32); o.rotation_euler = (ang, 0, 0); o.location = (0.02, -0.04, 0.06 + 0.18 * math.sin(ang))
    for k in range(3): sphere((0.12 + k * 0.05, -0.05, 0.06 + 0.18 * math.sin(ang) + (0.1 if up else -0.08)), (0.06, 0.02, 0.05), mat('tip', '#2a2a2e', 0.7), 12)
    render(sc, name)

def build_koi(name, base, spot):
    sc = reset(True); top_cam(sc, 0.9, 144)
    b_ = mat('k' + name, base, 0.45, 0.2); s_ = mat('s' + name, spot, 0.45, 0.2)
    sphere((0, 0, 0), (0.08, 0.26, 0.06), b_, 32)
    paint_on((0, 0, 0), (0.08, 0.26, 0.06), s_, (0.02, 0.05, 0.05), (0.07, 0.09, 0.09))
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.09, depth=0.12, location=(0, -0.3, 0)); o = bpy.context.object; o.scale = (1, 1, 0.2); o.rotation_euler = (math.radians(-90), 0, 0); o.data.materials.append(b_)
    for sx in (-1, 1): sphere((sx * 0.08, 0.08, 0), (0.06, 0.03, 0.01), b_, 12, rot=(0, 0, sx * 0.6))
    render(sc, 'koi_' + name)

JOBS = {'bg': build_bg, 'tube': build_tube, 'kakei': build_kakei, 'heron0': lambda: build_heron('heron0', True), 'heron1': lambda: build_heron('heron1', False),
        'koi_a': lambda: build_koi('a', '#f6f2ea', '#e8503a'), 'koi_b': lambda: build_koi('b', '#f08a2a', '#f6f2ea'), 'koi_c': lambda: build_koi('c', '#f6d040', '#f6f2ea')}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
