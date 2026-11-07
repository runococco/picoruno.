# Renders the layers for menko.html: a packed-earth playground seen from straight above with a chalk ring, and the round
# menko cards (five fronts with simple printed pictures, one plain back) that the game drops, flips and slides.
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




def W(px, py): return ((px - 360) / PXU, (640 - py) / PXU)

def build_bg():
    sc = reset(False)
    dirt = noise_mat('dirt', '#c8a878', '#b89464', 25, 0.95, 0.5)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.02)); o = bpy.context.object; o.scale = (8, 10, 1); o.data.materials.append(dirt)
    random.seed(3)
    peb = [mat('peb%d' % i, c, 0.8) for i, c in enumerate(['#9a8a74', '#b0a088', '#8a7a68'])]
    for i in range(70):
        x = random.uniform(-2.3, 2.3); y = random.uniform(-4, 4)
        if math.hypot(x, y - 0.0) < 2.0: continue
        sphere((x, y, 0), (random.uniform(.03, .07), random.uniform(.03, .06), .02), random.choice(peb), 12, rot=(0, 0, random.uniform(0, 3)))
    chalk = noise_mat('chalk', '#f4f0e6', '#e4dccc', 40, 0.95, 0.1)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.9, minor_radius=0.035, major_segments=160, minor_segments=8, location=(0, 0, 0)); t = bpy.context.object; t.scale = (1, 1, 0.1); t.data.materials.append(chalk)
    # a few leaves blown in from the edges
    lf = [mat('lf1', '#d8a040', 0.8), mat('lf2', '#c87838', 0.8), mat('lf3', '#88a048', 0.8)]
    for (x, y) in ((-1.9, 3.2), (2.0, -3.4), (1.8, 3.6), (-2.0, -3.0)):
        sphere((x, y, 0.01), (0.16, 0.08, 0.01), random.choice(lf), 16, rot=(0, 0, random.uniform(0, 3)))
    render(sc, 'bg')

def card_base(rim):
    board = noise_mat('board', '#e8dcc0', '#dccfb0', 30, 0.9, 0.2)
    o = cyl((0, 0, 0), 0.5, 0.04, board, 96); bevel(o, 0.008, 2)
    cyl((0, 0, 0.021), 0.5, 0.003, mat('rim' + rim, rim, 0.75), 96)
    cyl((0, 0, 0.023), 0.43, 0.003, mat('face' + rim, '#fff6e2', 0.8), 96)

def flat(loc, scale, m, rot=0, verts=48):
    o = cyl(loc, 1, 0.004, m, verts); o.scale = (scale[0], scale[1], 1); o.rotation_euler = (0, 0, rot)
    for p in o.data.polygons: p.use_smooth = False
    return o

def poly(pts, z, m):
    me = bpy.data.meshes.new('poly'); me.from_pydata([(x, y, z) for (x, y) in pts], [], [list(range(len(pts)))]); o = bpy.data.objects.new('poly', me)
    bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def tri(loc, r, sy, rot, m):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=r, depth=0.004, location=loc); c = bpy.context.object; c.scale = (1, sy, 1); c.rotation_euler = (0, 0, rot); c.data.materials.append(m); return c

def build_card(name):
    sc = reset(True); top_cam(sc, 1.2, 192)
    z = 0.027
    blk = mat('ink', '#2a1a10', 0.7)
    if name == 'back':
        board = noise_mat('board2', '#c8a070', '#b88f60', 30, 0.9, 0.2)
        o = cyl((0, 0, 0), 0.5, 0.04, board, 96); bevel(o, 0.008, 2)
        for r in (0.42, 0.3, 0.18):
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.012, major_segments=96, location=(0, 0, 0.021)); t = bpy.context.object; t.scale = (1, 1, 0.1); t.data.materials.append(mat('backline', '#8a5a32', 0.8))
        render(sc, 'back'); return
    if name == 'tora':
        card_base('#d8483a')
        o_ = mat('tor', '#f0a038', 0.7); w_ = mat('torw', '#fff6e2', 0.7)
        flat((0, -0.02, z), (0.28, 0.25), o_)
        for s in (-1, 1): flat((s * 0.2, 0.2, z), (0.08, 0.08), o_)
        for k in (-1, 0, 1): box((k * 0.07, 0.15 - abs(k) * 0.02, z + 0.003), (0.03, 0.09, 0.004), blk, 0.001)
        for s in (-1, 1):
            for k in range(2): box((s * (0.24 - k * 0.0), -0.02 - k * 0.07, z + 0.003), (0.08, 0.025, 0.004), blk, 0.001)
        flat((0, -0.1, z + 0.003), (0.12, 0.08), w_)
        for s in (-1, 1): flat((s * 0.1, 0.02, z + 0.004), (0.035, 0.035), blk)
        flat((0, -0.07, z + 0.005), (0.03, 0.02), blk)
    elif name == 'roket':
        card_base('#3a6ac8')
        flat((0, 0, z), (0.43, 0.43), mat('space', '#2a3a6a', 0.8), verts=96)
        wh = mat('rk', '#f6f2ea', 0.6); rd = mat('rkr', '#e8483a', 0.6)
        b = box((0, 0.02, z + 0.003), (0.13, 0.36, 0.006), wh, 0.03); b.rotation_euler = (0, 0, -0.5)
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.08, depth=0.006, location=(0.105, 0.2, z + 0.004)); c = bpy.context.object; c.rotation_euler = (0, 0, -0.5 - math.pi / 2 + math.pi); c.data.materials.append(rd)
        flat((0.01, 0.04, z + 0.006), (0.035, 0.035), mat('win', '#7ac8f0', 0.5))
        for s in (-1, 1): b = box((-0.07 + s * 0.07, -0.15 + s * -0.03, z + 0.003), (0.05, 0.1, 0.006), rd, 0.01); b.rotation_euler = (0, 0, -0.5)
        flat((-0.15, -0.22, z + 0.002), (0.05, 0.09), mat('fire', '#f69830', 0.7), rot=0.95)
        for (x, y) in ((-0.25, 0.2), (0.25, -0.15), (-0.15, -0.3), (0.28, 0.25)): flat((x, y, z + 0.002), (0.015, 0.015), mat('star', '#f6e070', 0.6))
    elif name == 'tai':
        card_base('#2a9a8a')
        rd = mat('tai', '#e85a4a', 0.65)
        flat((0.02, 0.04, z), (0.25, 0.15), rd)
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.12, depth=0.004, location=(-0.27, 0.04, z)); c = bpy.context.object; c.rotation_euler = (0, 0, math.pi); c.data.materials.append(rd)
        flat((0.16, 0.08, z + 0.003), (0.03, 0.03), blk)
        for (x, y, r) in ((0.22, 0.17, 0.03), (0.26, 0.24, 0.02), (0.21, 0.3, 0.015)): flat((x, y, z + 0.002), (r, r), mat('bub', '#7ac8f0', 0.6))
        poly([(-0.37, -0.2), (0.37, -0.2), (0.28, -0.3), (-0.28, -0.3)], z + 0.002, mat('wave', '#4a9ae0', 0.7))
    elif name == 'fuji':
        card_base('#e8a030')
        flat((0, 0, z - 0.001), (0.43, 0.43), mat('sky', '#a8d8f4', 0.8), verts=96)
        flat((0.18, 0.18, z), (0.09, 0.09), mat('sun', '#e8483a', 0.6))
        poly([(-0.34, -0.2), (0.34, -0.2), (0.07, 0.17), (-0.07, 0.17)], z + 0.002, mat('mt', '#4a6aa8', 0.7))
        poly([(-0.07, 0.17), (0.07, 0.17), (0.12, 0.1), (0.05, 0.12), (0.0, 0.08), (-0.05, 0.12), (-0.12, 0.1)], z + 0.003, mat('snow', '#f6f8fa', 0.7))
        poly([(-0.37, -0.2), (0.37, -0.2), (0.28, -0.3), (-0.28, -0.3)], z + 0.002, mat('lake', '#3a8ad0', 0.7))
    elif name == 'hoshi':   # the player's own card
        card_base('#e8b830')
        flat((0, 0, z - 0.001), (0.43, 0.43), mat('red', '#d8483a', 0.7), verts=96)
        st = mat('gold', '#f6d040', 0.55)
        for k in range(5):
            a = k / 5 * math.tau + math.pi / 2
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=0.004, location=(math.cos(a) * 0.17, math.sin(a) * 0.17, z + 0.002)); c = bpy.context.object; c.scale = (0.7, 1.6, 1); c.rotation_euler = (0, 0, a - math.pi / 2); c.data.materials.append(st)
        flat((0, 0, z + 0.002), (0.12, 0.12), st, rot=math.pi / 2, verts=5)
    render(sc, name)

JOBS = {'bg': build_bg}
for n in ('tora', 'roket', 'tai', 'fuji', 'hoshi', 'back'):
    JOBS[n] = (lambda n=n: build_card(n))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
