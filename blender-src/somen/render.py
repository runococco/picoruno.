# Renders the layers for somen.html: a summer garden with two split-bamboo flumes seen from straight above
# (full frame) and the noodle / tomato / cherry / leaf / chopstick sprites (same top-down camera).
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#e8f4ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # bright summer sun from the upper left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(12); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(22), math.radians(-24), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 400; a.data.size = 8; a.data.color = srgb('#e8f0ff')
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
LANES = (-0.85, 0.85)     # flume centre x
CATCH = -1.65             # catch line y (frame row 904)
RI, RO = 0.27, 0.31       # flume inner / outer radius

def halfpipe(x, y0, y1, ri, ro, m, segs=28):
    me = bpy.data.meshes.new('hp'); bm = bmesh.new()
    ang = [math.pi + math.pi * i / segs for i in range(segs + 1)]
    V = {}
    for yi, y in enumerate((y0, y1)):
        for side, r in (('i', ri), ('o', ro)):
            V[(yi, side)] = [bm.verts.new((x + r * math.cos(a), y, r * math.sin(a))) for a in ang]
    for k in range(segs):
        bm.faces.new((V[(0, 'i')][k], V[(0, 'i')][k + 1], V[(1, 'i')][k + 1], V[(1, 'i')][k]))
        bm.faces.new((V[(0, 'o')][k + 1], V[(0, 'o')][k], V[(1, 'o')][k], V[(1, 'o')][k + 1]))
        for yi in (0, 1): bm.faces.new((V[(yi, 'i')][k], V[(yi, 'o')][k], V[(yi, 'o')][k + 1], V[(yi, 'i')][k + 1]))
    for k in (0, segs): bm.faces.new((V[(0, 'i')][k], V[(1, 'i')][k], V[(1, 'o')][k], V[(0, 'o')][k]))
    bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('hp', me); bpy.context.collection.objects.link(o); o.data.materials.append(m); smooth(o); return o

def water_mat():
    m = bpy.data.materials.get('water')
    if m: return m
    m = mat('water', '#9ad4f0', 0.06, 0.5); b = m.node_tree.nodes['Principled BSDF']; b.inputs['Alpha'].default_value = 0.38
    return m

def cat_face_up(cx, cy, look):
    """calico cat head turned up to the camera; look = +1 means the face points toward +y"""
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); bk = mat('eye', '#1a1210', 0.9); pk = mat('catpk', '#f4a8a0', 0.8)
    sphere((cx, cy - look * 0.4, 0.0), (0.6, 0.45, 0.35), cw, 48)
    sphere((cx, cy, 0.25), (0.36, 0.32, 0.3), cw, 48)
    sphere((cx - 0.14, cy - look * 0.05, 0.47), (0.13, 0.12, 0.06), co, 24)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.11, depth=0.2, location=(cx + s_ * 0.24, cy - look * 0.12, 0.51)); e = bpy.context.object
        e.rotation_euler = (math.radians(30 * look), s_ * 0.35 * look, 0); e.data.materials.append(co if s_ < 0 else cw); smooth(e)
        sphere((cx + s_ * 0.13, cy + look * 0.11, 0.505), (0.042, 0.042, 0.02), bk, 16)
        sphere((cx + s_ * 0.21, cy + look * 0.2, 0.405), (0.06, 0.045, 0.02), pk, 12)
    sphere((cx, cy + look * 0.21, 0.475), (0.032, 0.024, 0.015), pk, 8)

def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#dff0e0'), 1)
    moss = noise_mat('moss', '#6a9a50', '#8ab868', 14, 0.9, 0.5)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.75)); f = bpy.context.object; f.scale = (14, 14, 1); f.data.materials.append(moss)
    random.seed(7)
    stone = noise_mat('stone', '#a8a49a', '#c8c4b8', 9, 0.8, 0.5)
    for (x, y, r) in ((-1.9, 2.6, .32), (2.0, 1.2, .28), (-2.0, -0.6, .3), (1.95, -2.1, .26), (0.0, 3.4, .22), (0.02, 0.6, .2), (0.0, -1.0, .18)):
        sphere((x, y, -0.75), (r, r * 0.85, r * 0.45), stone, 32, rot=(0, 0, random.random() * 3))
    peb = mat('peb', '#d8d4c8', 0.8)
    for i in range(40):
        x = random.uniform(-2.3, 2.3); y = random.uniform(-4, 4)
        if min(abs(x - l) for l in LANES) < 0.45: continue
        sphere((x, y, -0.74), (0.05, 0.04, 0.025), peb, 12, rot=(0, 0, random.random() * 3))
    gr = mat('grass', '#4a8a3a', 0.8)
    for i in range(26):
        x = random.choice((-1, 1)) * random.uniform(1.4, 2.4); y = random.uniform(-2.6, 4)
        for k in range(5): sphere((x + random.uniform(-.12, .12), y + random.uniform(-.12, .12), -0.68), (0.05, 0.16, 0.05), gr, 10, rot=(0, 0, random.uniform(-.6, .6)))
    # the two bamboo flumes, water running inside, crossed bamboo legs underneath
    bam = noise_mat('bamboo', '#5a9a3a', '#86c050', 3, 0.45, 0.15, detail=3)
    bamr = noise_mat('bamboo2', '#4a8a30', '#76b048', 3, 0.5, 0.15, detail=3)
    for lx in LANES:
        halfpipe(lx, -3.0, 4.6, RI, RO, bam)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(lx, 0.8, -0.16)); w = bpy.context.object; w.scale = (2 * math.sqrt(RI * RI - 0.16 ** 2) - 0.01, 7.6, 1); w.data.materials.append(water_mat())
        for ly in (2.4, -0.4):
            for s_ in (-1, 1): cyl((lx, ly, -0.5), 0.04, 1.05, bamr, 16, rot=(0, math.radians(90 + s_ * 28), 0))
        for ny in (3.6, 1.0, -2.2): cyl((lx, ny, -0.29), RO + 0.012, 0.035, bamr, 32, rot=(math.radians(90), 0, 0)).scale = (1, 1, 1)
    # the tub at the end, the tsuyu bowl and the cat waiting for misses
    oke = wood('oke', '#c89860', '#e0b880'); hoop = mat('hoop', '#b07840', 0.4, 0.5)
    cyl((0, -3.75, -0.55), 1.0, 0.5, oke, 64); cyl((0, -3.75, -0.29), 0.9, 0.01, mat('tubw', '#8ac8e0', 0.05, 0.6), 64)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, location=(0, -3.75, -0.36)); h = bpy.context.object; h.data.materials.append(hoop)
    glass = mat('glass', '#d8eef8', 0.08, 0.6); glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3
    cyl((-1.75, -3.35, -0.55), 0.48, 0.3, glass, 48); cyl((-1.75, -3.35, -0.395), 0.43, 0.01, mat('tsuyu', '#6a3a18', 0.12, 0.5), 48)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.48, minor_radius=0.025, location=(-1.75, -3.35, -0.4)); h = bpy.context.object; h.data.materials.append(glass)
    for (dx, dy) in ((-0.12, 0.1), (0.05, 0.16), (0.14, -0.02), (-0.03, -0.1)): cyl((-1.75 + dx, -3.35 + dy, -0.385), 0.035, 0.01, mat('negi', '#9ad060', 0.5), 12)
    sphere((-1.55, -3.5, -0.385), (0.07, 0.07, 0.02), mat('wasabi', '#a8c860', 0.8), 16)
    cat_face_up(1.72, -3.45, 1)
    render(sc, 'bg')
    META['lanes'] = [proj(l, 0, 0)[0] for l in LANES]; META['catch'] = proj(0, CATCH, 0)[1]
    META['bowl'] = proj(-1.75, -3.35, -0.4); META['tub'] = proj(0, -3.75, -0.3); META['cat'] = proj(1.72, -3.45, 0.5)
    META['flumeEnd'] = proj(0, -3.0, 0)[1]; META['waterW'] = 2 * math.sqrt(RI * RI - 0.16 ** 2) * PXU

def strands(n, cols, length=0.5, width=0.16, seed=1):
    random.seed(seed)
    for i in range(n):
        cu = bpy.data.curves.new('s', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.011; cu.bevel_resolution = 2
        sp = cu.splines.new('POLY'); pts = 9; sp.points.add(pts - 1)
        bx = random.uniform(-width / 2, width / 2); ph = random.uniform(0, 6); amp = random.uniform(0.01, 0.03)
        for k in range(pts):
            t = k / (pts - 1); y = (t - 0.5) * length * random.uniform(0.9, 1.05)
            x = bx * (1 - 0.35 * math.sin(t * math.pi)) + amp * math.sin(ph + t * 7)
            sp.points[k].co = (x, y, random.uniform(0.0, 0.03) + 0.02 * math.sin(t * math.pi), 1)
        o = bpy.data.objects.new('s', cu); bpy.context.collection.objects.link(o); o.data.materials.append(cols[i % len(cols)])

def build_sprites():
    sc = reset(True); strands(16, [mat('noodle', '#fbf8ee', 0.35, 0.4, sss=0.3)], seed=3)
    sprite_cam(sc, 0.8, 160); SPR['item'] = {'res': 160, 'pxu': 200.0}
    render(sc, 'somen')
    sc = reset(True); noodle = mat('noodle', '#fbf8ee', 0.35, 0.4, sss=0.3); pink = mat('pinkn', '#f4a0b4', 0.35, 0.4, sss=0.3); grn = mat('grnn', '#a8d888', 0.35, 0.4, sss=0.3)
    strands(16, [noodle, pink, noodle, grn, noodle, noodle, pink, noodle], seed=5); sprite_cam(sc, 0.8, 160); render(sc, 'iro')
    sc = reset(True)   # cherry tomato with its green calyx
    sphere((0, 0, 0), (0.12, 0.12, 0.11), mat('tomato', '#e8382a', 0.22, 0.6), 48)
    cg = mat('calyx', '#4a8a2a', 0.6)
    for k in range(5):
        a = k / 5 * math.tau; sphere((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.105), (0.05, 0.016, 0.01), cg, 12, rot=(0, 0, a))
    cyl((0, 0, 0.12), 0.01, 0.04, cg, 8); sprite_cam(sc, 0.8, 160); render(sc, 'tomato')
    sc = reset(True)   # a pair of cherries
    ch = mat('cherry', '#c8182a', 0.18, 0.7); stem = mat('stem', '#6a8a3a', 0.6)
    for (x, y) in ((-0.07, -0.08), (0.07, -0.05)):
        sphere((x, y, 0), (0.075, 0.075, 0.07), ch, 40)
        cu = bpy.data.curves.new('st', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        sp.bezier_points[0].co = (x, y, 0.06); sp.bezier_points[1].co = (0.02, 0.17, 0.1)
        for p in sp.bezier_points: p.handle_left_type = p.handle_right_type = 'AUTO'
        o = bpy.data.objects.new('st', cu); bpy.context.collection.objects.link(o); o.data.materials.append(stem)
    sphere((0.07, 0.19, 0.1), (0.06, 0.025, 0.006), mat('cleaf', '#4a9a3a', 0.6), 12, rot=(0, 0, 0.5))
    sprite_cam(sc, 0.8, 160); render(sc, 'cherry')
    sc = reset(True)   # a little sprig of bamboo leaves (do not catch)
    lf = mat('leafg', '#4a9a32', 0.5); vein = mat('vein', '#2f6a22', 0.6)
    for (a_, L, ox, oy) in ((-0.55, 0.32, 0.0, 0.0), (0.5, 0.28, 0.0, -0.03), (0.05, 0.22, 0.0, 0.02)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(0, 0, 0)); o = bpy.context.object
        o.scale = (0.055, L / 2, 0.01)
        bm = bmesh.new(); bm.from_mesh(o.data)
        for v in bm.verts: v.co.x *= max(0.15, 1 - max(0, v.co.y) * 0.7)       # pointed tip
        bm.to_mesh(o.data); bm.free(); smooth(o); o.data.materials.append(lf)
        o.location = (ox + math.sin(-a_) * -L / 2 * -1, oy + math.cos(a_) * L / 2, 0); o.rotation_euler = (0, 0, a_)
        v = sphere((0, 0, 0.007), (0.004, L / 2 * 0.95, 0.002), vein, 8); v.location = o.location; v.rotation_euler = (0, 0, a_)
    cyl((0, -0.06, 0), 0.008, 0.14, vein, 8, rot=(math.radians(90), 0, 0))
    sprite_cam(sc, 0.8, 160); render(sc, 'leaf')
    sc = reset(True)   # one chopstick lying along y, tip at the bottom
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.016, radius2=0.034, depth=1.4, location=(0, 0, 0), rotation=(math.radians(-90), 0, 0))
    o = bpy.context.object; o.data.materials.append(wood('hashi', '#d8b078', '#e8c890')); smooth(o)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.0285, radius2=0.035, depth=0.4, location=(0, 0.5, 0), rotation=(math.radians(-90), 0, 0))
    o = bpy.context.object; o.scale = (1.06, 1.0, 1.06); o.data.materials.append(mat('urushi', '#a02a20', 0.3, 0.5)); smooth(o)
    sprite_cam(sc, 1.6, 320); SPR['hashi'] = {'res': 320, 'pxu': 200.0, 'tip': [160.0, 160 + 0.7 * 200]}
    render(sc, 'hashi')

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
