# Renders the layers for asagao.html. The garden bed is a full-frame layer; the pieces are sprites rendered
# with a camera at the same 65 deg elevation, centred on the tile's ground point.
# python3 render.py <what> <outdir>      what = all | bg,sun,mirror_a,mirror_b,bud,bloom_blue,bloom_pink,bloom_purple,rock (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 65.0; TZ = 0.0     # camera: ortho height 8 units looking down at 65 deg, target (0,0,0)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#d8ecff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # early morning sun low from the upper left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.4; s.data.angle = math.radians(10); s.data.color = srgb('#fff0d0')
    s.rotation_euler = Euler((math.radians(45), math.radians(-25), math.radians(-140)))
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

COLS, ROWS, T = 6, 8, 0.575          # board size and tile size (units)
def tile_w(i, j): return ((i - (COLS - 1) / 2) * T, ((ROWS - 1) / 2 - j) * T)

def build_bg():
    sc = reset(False)
    grass = noise_mat('grass', '#8ab85a', '#a4c86a', 10, 0.9, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.02)); g = bpy.context.object; g.scale = (8, 12, 1); g.data.materials.append(grass)
    soil = noise_mat('soil', '#7a5a3e', '#8e6c4a', 14, 0.95, 0.6)
    W, H = COLS * T, ROWS * T
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.0)); s = bpy.context.object; s.scale = (W, H, 0.06); s.data.materials.append(soil)
    # soft furrows: one slightly raised mound per tile
    sm = noise_mat('soil2', '#86664a', '#9a7856', 18, 0.95, 0.7)
    for j in range(ROWS):
        for i in range(COLS):
            x, y = tile_w(i, j); o = sphere((x, y, 0.025), (T * 0.42, T * 0.42, 0.035), sm, 24)
    # wooden bed frame
    wd = wood('bed', '#b88a5a', '#9a6e44')
    for (x, y, sx, sy) in ((0, H / 2 + 0.06, W + 0.24, 0.12), (0, -H / 2 - 0.06, W + 0.24, 0.12), (W / 2 + 0.06, 0, 0.12, H), (-W / 2 - 0.06, 0, 0.12, H)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.06)); b = bpy.context.object; b.scale = (sx, sy, 0.2); b.data.materials.append(wd); bevel(b, 0.02)
    # around the bed: clover, pebbles, a watering can and a bamboo fence at the top
    random.seed(7); clov = mat('clover', '#5a9a3a', 0.7, 0.2); peb = noise_mat('pebble', '#b8b0a4', '#d0c8bc', 6, 0.7, 0.3)
    for k in range(40):
        x, y = random.uniform(-2.3, 2.3), random.uniform(-4.4, 4.4)
        if abs(x) < W / 2 + 0.2 and abs(y) < H / 2 + 0.2: continue
        if random.random() < 0.5: sphere((x, y, 0.0), (0.06, 0.05, 0.03), peb, 12, (0, 0, random.random() * 3))
        else:
            for a in range(3): sphere((x + math.cos(a * 2.1) * 0.05, y + math.sin(a * 2.1) * 0.05, 0.02), (0.05, 0.05, 0.01), clov, 12)
    bam = noise_mat('bamboo', '#b8a45a', '#ccb86a', 6, 0.5, 0.2)
    for k in range(-12, 13): cyl((k * 0.2, H / 2 + 0.6, 0.35), 0.05, 0.7, bam, 12)
    for z in (0.25, 0.55): cyl((0, H / 2 + 0.55, z), 0.035, 5.2, bam, 12, (0, math.radians(90), 0))
    can = mat('can', '#5aa0d8', 0.35, 0.5)
    cyl((-1.95, -H / 2 - 0.55, 0.18), 0.17, 0.36, can, 32); cyl((-1.7, -H / 2 - 0.55, 0.3), 0.03, 0.4, can, 12, (0, math.radians(55), 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.02, location=(-1.95, -H / 2 - 0.55, 0.42), rotation=(math.radians(90), 0, 0)); bpy.context.object.data.materials.append(can)
    render(sc, 'bg')

SPR = {}
def sprite_cam(sc, scale, res, elev=ELEV):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(elev); d = 30; loc = Vector((0, -math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (-loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()

def leaves(n=2, s=1.0):
    lf = noise_mat('leaf', '#4a8a2e', '#5aa03a', 8, 0.6, 0.3)
    for k in range(n):
        a = math.radians(200 + k * 140 / max(1, n - 1)) if n > 1 else 0
        pts = []
        for t in range(24):
            u = t / 24 * math.tau; r = 0.13 * s * (1 - math.sin(u) * 0.4) * (1 + 0.25 * math.cos(2 * u))
            pts.append((math.cos(u) * r, math.sin(u) * r * 1.2 + 0.12 * s))
        me = bpy.data.meshes.new('l'); bm = bmesh.new(); c0 = bm.verts.new((0, 0.12 * s, 0)); vs = [bm.verts.new((x, y, 0)) for x, y in pts]
        for q in range(len(vs)): bm.faces.new((c0, vs[q], vs[(q + 1) % len(vs)]))
        bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('l', me); bpy.context.collection.objects.link(o); o.data.materials.append(lf)
        o.modifiers.new('s', 'SOLIDIFY').thickness = 0.01
        o.rotation_euler = (math.radians(25), 0, a - math.radians(90)); o.location = (0, 0, 0.03)

def build_bud():
    sc = reset(True); leaves(3)
    st = mat('stem', '#5a9a3a', 0.6); cyl((0, 0, 0.12), 0.015, 0.24, st, 8)
    bud = noise_mat('bud', '#6a7ab8', '#9aa8e0', 12, 0.5, 0.2)
    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.06, radius2=0.0, depth=0.22, location=(0, 0, 0.33)); b = bpy.context.object; b.data.materials.append(bud)
    sw = b.modifiers.new('tw', 'SIMPLE_DEFORM'); sw.deform_method = 'TWIST'; sw.angle = math.radians(220); sw.deform_axis = 'Z'
    b.modifiers.new('ss', 'SUBSURF').levels = 2; smooth(b)
    cal = mat('calyx', '#4a8a2e', 0.6)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.05, radius2=0.025, depth=0.07, location=(0, 0, 0.245)); bpy.context.object.data.materials.append(cal)
    sprite_cam(sc, 0.66, 160); render(sc, 'bud')

BLOOM = {'blue': ('#3a6ad8', '#6a9af0'), 'pink': ('#e8508a', '#f08ab0'), 'purple': ('#8a4ac8', '#b07ae0')}
def build_bloom(col):
    sc = reset(True); leaves(3)
    st = mat('stem', '#5a9a3a', 0.6); cyl((0, 0, 0.1), 0.015, 0.2, st, 8)
    c1, c2 = BLOOM[col]; pet = noise_mat('petal_' + col, c1, c2, 5, 0.55, 0.15); wh = mat('throat', '#fbf8f0', 0.6, 0.1, sss=0.2)
    # trumpet: a flared funnel facing up toward the camera
    prof = [(0.02, 0.2), (0.04, 0.24), (0.08, 0.28), (0.15, 0.31), (0.22, 0.325), (0.25, 0.33)]
    me = bpy.data.meshes.new('f'); bm = bmesh.new(); rings = []
    for (r, z) in prof:
        ring = []
        for k in range(40):
            a = k / 40 * math.tau; rr = r * (1 + 0.06 * math.cos(5 * a)) if r > 0.1 else r
            ring.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z)))
        rings.append(ring)
    for q in range(len(rings) - 1):
        for k in range(40): bm.faces.new((rings[q][k], rings[q][(k + 1) % 40], rings[q + 1][(k + 1) % 40], rings[q + 1][k]))
    bm.to_mesh(me); bm.free(); f = bpy.data.objects.new('f', me); bpy.context.collection.objects.link(f)
    f.data.materials.append(pet); f.modifiers.new('s', 'SOLIDIFY').thickness = 0.012; f.modifiers.new('ss', 'SUBSURF').levels = 1; smooth(f)
    f.rotation_euler = (math.radians(-25), 0, 0)
    # white throat and five pale rays
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.02, radius2=0.1, depth=0.09, location=(0, 0, 0.26)); t = bpy.context.object; t.data.materials.append(wh); smooth(t)
    t.rotation_euler = (math.radians(-25), 0, 0); t.location = (0, 0.03, 0.27)
    ray = mat('ray', '#f4ecf8', 0.6, 0.1)
    for k in range(5):
        a = k / 5 * math.tau + 0.3; cu = bpy.data.curves.new('r', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008
        sp = cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co = (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.285, 1); sp.points[1].co = (math.cos(a) * 0.23, math.sin(a) * 0.23, 0.335, 1)
        o = bpy.data.objects.new('r', cu); bpy.context.collection.objects.link(o); o.data.materials.append(ray); o.rotation_euler = (math.radians(-25), 0, 0)
    sprite_cam(sc, 0.66, 160); render(sc, 'bloom_' + col)

def build_mirror(name, rot):
    sc = reset(True)
    wd = wood('frame', '#c08a54', '#9a6a3e'); gl = mat('glass', '#e8f4ff', 0.03, 1.0); gl.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 1.0
    root = bpy.data.objects.new('m', None); bpy.context.collection.objects.link(root)
    o = cyl((0, 0, 0.0), 0.24, 0.03, gl, 48, (math.radians(90), 0, 0)); o.parent = root; o.location = (0, 0, 0.3)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.245, minor_radius=0.028, location=(0, 0, 0.3), rotation=(math.radians(90), 0, 0)); fr = bpy.context.object; fr.data.materials.append(wd); fr.parent = root
    s = cyl((0, 0, 0.05), 0.02, 0.12, wd, 12); s.parent = root
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.02)); b = bpy.context.object; b.scale = (0.28, 0.12, 0.04); b.data.materials.append(wd); bevel(b, 0.015); b.parent = root
    root.rotation_euler = (0, 0, math.radians(rot))
    sprite_cam(sc, 0.66, 160); render(sc, name)

def build_sun():
    sc = reset(True)
    y = mat('sunface', '#ffc83a', 0.5, 0.2, emit=('#ffb020', 0.6)); ry = mat('sunray', '#ff9a2a', 0.5, 0.2, emit=('#ff8a20', 0.5))
    ink = mat('ink', '#2a1a12', 0.3, 0.5); pk = mat('cheek', '#ff8a6a', 0.7)
    e = math.radians(ELEV); fwd = Vector((0, -math.cos(e), math.sin(e)))   # toward the camera
    sphere((0, 0, 0.3), (0.26, 0.26, 0.26), y, 48)
    for k in range(10):
        a = k / 10 * math.tau; d = Vector((math.cos(a), 0, math.sin(a)))
        right = Vector((1, 0, 0)); up = fwd.cross(right).normalized(); dirv = (right * math.cos(a) + up * math.sin(a)).normalized()
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.06, depth=0.14, location=Vector((0, 0, 0.3)) + dirv * 0.32)
        c = bpy.context.object; c.rotation_euler = dirv.to_track_quat('Z', 'Y').to_euler(); c.data.materials.append(ry); smooth(c)
    right = Vector((1, 0, 0)); up = fwd.cross(right).normalized()
    for s_ in (-1, 1):
        sphere(Vector((0, 0, 0.3)) + fwd * 0.245 + right * s_ * 0.09 + up * 0.03, (0.03, 0.03, 0.03), ink, 16)
        sphere(Vector((0, 0, 0.3)) + fwd * 0.23 + right * s_ * 0.15 - up * 0.05, (0.045, 0.045, 0.02), pk, 16)
    sprite_cam(sc, 1.0, 180); render(sc, 'sun')

def build_rock():
    sc = reset(True)
    rk = noise_mat('rock', '#8a847a', '#a49e92', 6, 0.85, 0.6); mo = noise_mat('moss', '#5a8a3a', '#7aa84a', 20, 0.9, 0.5)
    o = sphere((0, 0, 0.1), (0.22, 0.19, 0.17), rk, 32, (0, 0, 0.4))
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('rk', 'CLOUDS'); tx.noise_scale = 0.2; d.texture = tx; d.strength = 0.05
    sphere((-0.04, 0.03, 0.22), (0.12, 0.1, 0.05), mo, 16)
    sprite_cam(sc, 0.66, 160); render(sc, 'rock')

JOBS = {'bg': build_bg, 'sun': build_sun, 'mirror_a': lambda: build_mirror('mirror_a', 45), 'mirror_b': lambda: build_mirror('mirror_b', -45),
        'bud': build_bud, 'rock': build_rock}
for k in BLOOM: JOBS['bloom_' + k] = (lambda k=k: build_bloom(k))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = {'pxu': PXU, 'elev': ELEV, 'cols': COLS, 'rows': ROWS, 'tile': T * PXU,
        'origin': [round(v, 1) for v in proj(*tile_w(0, 0), 0)], 'step': [T * PXU, T * PXU * math.sin(math.radians(ELEV))],
        'sprite': {'res': 160, 'scale': 0.66}, 'sun': {'res': 180, 'scale': 1.0}}
json.dump(meta, open(MP, 'w'))
