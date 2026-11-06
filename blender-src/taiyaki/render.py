# Renders the layers for taiyaki.html. Full-frame layers share ONE ortho camera (720x1280, 160 px/unit, 55 deg down);
# the fish / fillings are rendered at mold 0 and moved to the other molds in the game (ortho: a pure translation).
# python3 render.py <what> <outdir>      what = all | street,counter,batter,fish_raw,fish_gold,fish_burnt,anko,custard,matcha,tanuki,... (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 55.0; TZ = 0.0     # camera: ortho height 8 units looking down at 55 deg, target (0,0,0)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#ffd8a8'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.45
    # warm yatai bulb above the counter + soft key from the front left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(35), math.radians(-20), math.radians(-20)))
    bpy.ops.object.light_add(type='POINT', location=(0, 1.2, 3.2))
    p = bpy.context.object; p.data.energy = 900; p.data.color = srgb('#ffc880'); p.data.shadow_soft_size = 0.6
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

# ---------------------------------------------------------------- layout (world units)
MOLDS = [(-1.02, 0.85), (1.02, 0.85), (-1.02, -1.0), (1.02, -1.0)]
IRON_Z = 0.3; CAV = 0.13                       # iron top height, cavity depth
TUBS = {'anko': (-1.45, -3.25), 'custard': (0.0, -3.25), 'matcha': (1.45, -3.25)}

def fish_pts(s=1.0):
    pts = []
    for k in range(0, 21):                      # upper body: nose -> back
        a = math.radians(k * 150 / 20); pts.append((0.12 + 0.7 * math.cos(a), 0.4 * math.sin(a)))
    pts += [(-0.64, 0.17), (-0.9, 0.42), (-0.82, 0.05), (-0.82, -0.05), (-0.9, -0.42), (-0.64, -0.17)]
    for k in range(0, 21):                      # lower body: back -> nose
        a = math.radians(210 + k * 150 / 20); pts.append((0.12 + 0.7 * math.cos(a), 0.4 * math.sin(a)))
    return [(x * s, y * s) for x, y in pts]

def fish_curve(name, s, extrude, bevel_d, loc, m=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'; cu.extrude = extrude; cu.bevel_depth = bevel_d; cu.bevel_resolution = 4
    sp = cu.splines.new('POLY'); pts = fish_pts(s); sp.points.add(len(pts) - 1); sp.use_cyclic_u = True
    for j, (x, y) in enumerate(pts): sp.points[j].co = (x, y, 0, 1)
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob); ob.location = loc
    if m: ob.data.materials.append(m)
    return ob

def to_mesh(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH'); return bpy.context.object

def iron_mat():
    m = bpy.data.materials.get('iron')
    if m: return m
    m = noise_mat('iron', '#262220', '#3a3430', 30, 0.55, 0.25)
    m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.7
    return m

def build_iron():
    im = iron_mat()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.08, IRON_Z / 2)); pl = bpy.context.object; pl.scale = (4.35, 4.0, IRON_Z); bpy.ops.object.transform_apply(scale=True)
    bevel(pl, 0.06, 3)
    for i, (x, y) in enumerate(MOLDS):
        cut = to_mesh(fish_curve('cut%d' % i, 1.06, 0.2, 0.06, (x, y, IRON_Z)))
        b = pl.modifiers.new('cut%d' % i, 'BOOLEAN'); b.object = cut; b.operation = 'DIFFERENCE'; cut.hide_render = True
    pl.data.materials.append(im)
    # handles and the hinge
    hd = wood('handle', '#7a4a2a', '#5a3420')
    for s in (-1, 1):
        cyl((s * 2.55, -0.08, IRON_Z * .6), 0.07, 0.8, im, 16, (0, math.radians(90), 0))
        cyl((s * 3.1, -0.08, IRON_Z * .6), 0.1, 0.6, hd, 24, (0, math.radians(90), 0))
    # burner glow peeking out under the iron
    fl = mat('flame', '#5a8aff', 0.5, 0.0, emit=('#4a7aff', 6.0))
    for k in range(26):
        x = -2.0 + k * 0.16; sphere((x, -2.1, 0.03), (0.05, 0.05, 0.09), fl, 10)

def build_counter_layer():
    sc = reset(True)
    wd = wood('counter', '#c08a54', '#a0703e')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.2, -0.1)); c = bpy.context.object; c.scale = (8, 8, 0.2); c.data.materials.append(wd)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.72, 0.06)); e = bpy.context.object; e.scale = (8, 0.16, 0.12); e.data.materials.append(wood('edge', '#8a5a34', '#6a4426')); bevel(e, 0.03)
    build_iron()
    # filling tubs
    tub = wood('tub', '#c89a60', '#a87a44'); band = mat('band', '#3a3028', 0.5, 0.4); bowl = mat('bowl', '#f6f0e4', 0.3, 0.5); cel = mat('celadon', '#9ac0a0', 0.3, 0.5)
    for k, (x, y) in TUBS.items():
        if k == 'anko':
            cyl((x, y, 0.22), 0.56, 0.44, tub, 48)
            for z in (0.08, 0.36): bpy.ops.mesh.primitive_torus_add(major_radius=0.565, minor_radius=0.025, location=(x, y, z)); bpy.context.object.data.materials.append(band)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(x, y, 0.42)); b = bpy.context.object; b.scale = (0.58, 0.58, 0.42); smooth(b)
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
            for v in b.data.vertices: v.select = v.co.z > 0.0
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
            sd = b.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.04; b.data.materials.append(bowl if k == 'custard' else cel)
        fill = {'anko': noise_mat('anko', '#3a1a16', '#5a2a22', 22, 0.35, 0.8, 0.3, 0.75), 'custard': mat('custardf', '#f4d27a', 0.25, 0.4, sss=0.2),
                'matcha': mat('matchaf', '#8ab04a', 0.3, 0.4, sss=0.2)}[k]
        o = sphere((x, y, 0.38), (0.5, 0.5, 0.08), fill, 48)
        if k == 'anko':
            for j in range(18):
                a = random.random() * math.tau; r = random.random() * 0.4; sphere((x + math.cos(a) * r, y + math.sin(a) * r, 0.44), (0.05, 0.035, 0.03), fill, 10, (0, 0, a))
        # wooden spatula resting in it
        sp = wood('spat', '#d8b07a', '#c0965e')
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 0.25, y + 0.1, 0.6)); h = bpy.context.object; h.scale = (0.08, 0.7, 0.03); h.rotation_euler = (math.radians(-30), 0, math.radians(-30)); h.data.materials.append(sp); bevel(h, 0.01)
    render(sc, 'counter')

def build_street():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#2e2c4e'), 1); sc.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    st = noise_mat('paving', '#3a3848', '#4a4658', 4, 0.8, 0.5)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5, -1.6)); g = bpy.context.object; g.scale = (10, 6, 1); g.data.materials.append(st)
    # a wall across the street with warm windows, and red paper lanterns
    wl = noise_mat('wall', '#4a3a3a', '#5a4644', 6, 0.9, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7.2, 0)); w = bpy.context.object; w.scale = (10, 0.2, 6); w.data.materials.append(wl)
    win = mat('win', '#ffcf80', 0.5, 0.1, emit=('#ffb860', 1.6)); kr = mat('koshi', '#2a1e1a', 0.7)
    for x in (-2.2, 0.0, 2.2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 7.05, 0.3)); o = bpy.context.object; o.scale = (1.4, 0.05, 1.2); o.data.materials.append(win)
        for k in range(-3, 4): cyl((x + k * 0.2, 7.0, 0.3), 0.025, 1.2, kr, 8)
    red = mat('chochin', '#e8402a', 0.6, 0.1, emit=('#ff5a2a', 1.3)); blk = mat('chtop', '#2a2020', 0.6)
    for x in (-1.75, 1.75):
        sphere((x, 3.1, 0.55), (0.3, 0.3, 0.4), red, 32)
        cyl((x, 3.1, 0.97), 0.16, 0.06, blk, 24); cyl((x, 3.1, 0.13), 0.16, 0.06, blk, 24)
    render(sc, 'street')

def fish_mat(name, c1, c2):
    m = bpy.data.materials.get(name)
    if m: return m
    m = noise_mat(name, c1, c2, 7, 0.55, 0.25, 0.3, 0.75)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 16
    nt.links.new(nt.nodes['Texture Coordinate'].outputs['Object'], vo.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.invert = True
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

FISH = {'fish_raw': ('#ead09a', '#f2dcaa'), 'fish_gold': ('#cc8238', '#dc9846'), 'fish_burnt': ('#3a2214', '#5a3420')}
def build_fish(name):
    sc = reset(True)
    x, y = MOLDS[0]; m = fish_mat(name, *FISH[name])
    f = fish_curve('fish', 1.0, 0.05, 0.11, (x, y, IRON_Z - CAV + 0.09), m)
    zt = IRON_Z - CAV + 0.09 + 0.16
    # face and fins pressed into the top
    sphere((x + 0.6, y + 0.1, zt - 0.02), (0.075, 0.075, 0.04), m, 16)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.018, location=(x + 0.6, y + 0.1, zt - 0.01)); bpy.context.object.data.materials.append(m)
    for k in range(3):   # gill and fin ridges
        cu = bpy.data.curves.new('g', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.016
        spn = cu.splines.new('NURBS'); pts = [(x + 0.38 - k * 0.12 + 0.03 * math.sin(a), y + 0.28 * math.cos(a) - 0.02, zt - 0.03) for a in (0.4, 1.2, 1.9, 2.7)]
        spn.points.add(len(pts) - 1); spn.use_endpoint_u = True; spn.order_u = 3
        for j, p in enumerate(pts): spn.points[j].co = (*p, 1)
        ob = bpy.data.objects.new('g', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
        if k > 0: ob.hide_render = True
    for k in range(4):
        a = math.radians(-30 + k * 20); cu = bpy.data.curves.new('t', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.014
        spn = cu.splines.new('POLY'); spn.points.add(1)
        spn.points[0].co = (x - 0.6, y, zt - 0.03, 1); spn.points[1].co = (x - 0.6 - 0.24 * math.cos(a), y + 0.3 * math.sin(a), zt - 0.04, 1)
        ob = bpy.data.objects.new('t', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    holdout_iron()
    render(sc, name)

def holdout_iron():
    # the iron in front of the fish edges hides them exactly like in the real mold
    build_iron()
    for o in list(bpy.context.scene.objects):
        if o.type == 'MESH' and o.data.materials and o.data.materials[0].name in ('iron', 'handle', 'flame'): o.is_holdout = True

def build_batter():
    sc = reset(True)
    x, y = MOLDS[0]; m = mat('batter', '#f4e2b4', 0.15, 0.6, sss=0.3)
    fish_curve('bat', 1.04, 0.01, 0.0, (x, y, IRON_Z - 0.035), m)
    holdout_iron(); render(sc, 'batter')

def build_filling(kind):
    sc = reset(True)
    x, y = MOLDS[0]; z = IRON_Z - 0.02
    if kind == 'anko':
        m = noise_mat('anko', '#3a1a16', '#5a2a22', 22, 0.35, 0.8, 0.3, 0.75)
        sphere((x + 0.05, y, z), (0.36, 0.22, 0.09), m, 32)
        random.seed(3)
        for j in range(12): a = random.random() * math.tau; r = random.random(); sphere((x + 0.05 + math.cos(a) * .28 * r, y + math.sin(a) * .16 * r, z + 0.07), (0.045, 0.032, 0.03), m, 10, (0, 0, a))
    else:
        m = mat(kind + 'f', '#f4d27a' if kind == 'custard' else '#8ab04a', 0.25, 0.4, sss=0.2)
        sphere((x + 0.05, y, z), (0.36, 0.22, 0.1), m, 32)
        sphere((x + 0.0, y + 0.04, z + 0.07), (0.16, 0.1, 0.05), m, 24)
    render(sc, kind)

# ---------------------------------------------------------------- customers (sprite camera, slightly from above)
SPR = {}
def sprite_cam(sc, scale, res, elev):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(elev); d = 30; loc = Vector((0, -math.cos(e) * d, math.sin(e) * d + 0.6))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (Vector((0, 0, 0.6)) - loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    m = c.matrix_world.to_3x3(); t = c.matrix_world.translation
    return lambda p: (res / 2 + (Vector(p) - t).dot(m.col[0]) * res / scale, res / 2 - (Vector(p) - t).dot(m.col[1]) * res / scale)

ANIMALS = {   # fur, belly/face, ear inner, ear kind, extra
    'tanuki': ('#8a6a4a', '#e8d8c0', '#5a4030', 'round'),
    'neko': ('#f6f0e4', '#fffaf2', '#f0b0a0', 'cat'),
    'usagi': ('#f8f4ee', '#ffffff', '#f4b8b8', 'long'),
    'kitsune': ('#e8883a', '#fff4e4', '#3a2a22', 'fox'),
}
def build_animal(kind):
    sc = reset(True)
    fur, belly, inner, ears = ANIMALS[kind]
    fm = mat('fur_' + kind, fur, 0.85, 0.1, sss=0.15); bm_ = mat('belly_' + kind, belly, 0.85, 0.1, sss=0.15); im = mat('inner_' + kind, inner, 0.8, 0.1)
    ink = mat('ink', '#2a1a12', 0.3, 0.5); pink = mat('cheek', '#f4a0a0', 0.8, 0.1)
    sphere((0, 0, 0.0), (0.62, 0.5, 0.6), fm, 48)                         # shoulders / body (cut by the counter)
    sphere((0, -0.3, 0.05), (0.38, 0.25, 0.45), bm_, 32)
    hz = 0.95; sphere((0, 0, hz), (0.5, 0.44, 0.44), fm, 48)               # head
    sphere((0, -0.3, hz - 0.1), (0.26, 0.16, 0.18), bm_, 32)               # muzzle
    if kind == 'tanuki':
        for s in (-1, 1): sphere((s * 0.19, -0.33, hz + 0.04), (0.15, 0.06, 0.11), mat('mask', '#4a3424', 0.85), 24)
    sphere((0, -0.46, hz - 0.06), (0.055, 0.04, 0.04), ink, 16)            # nose
    for s in (-1, 1):
        sphere((s * 0.19, -0.4, hz + 0.05), (0.05, 0.03, 0.05), ink, 16)  # solid dot eyes
        sphere((s * 0.3, -0.33, hz - 0.1), (0.07, 0.03, 0.045), pink, 16)
        if ears == 'round':
            sphere((s * 0.33, 0.0, hz + 0.36), (0.14, 0.08, 0.13), fm, 24); sphere((s * 0.33, -0.05, hz + 0.36), (0.08, 0.04, 0.08), im, 16)
        elif ears == 'long':
            sphere((s * 0.17, 0.02, hz + 0.68), (0.1, 0.07, 0.36), fm, 24, (0, s * 0.15, 0)); sphere((s * 0.17, -0.04, hz + 0.66), (0.055, 0.03, 0.27), im, 16, (0, s * 0.15, 0))
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.17, depth=0.34 if ears == 'fox' else 0.26, location=(s * 0.3, 0.0, hz + 0.43))
            e = bpy.context.object; e.rotation_euler = (0, s * 0.35, 0); e.data.materials.append(fm); smooth(e)
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.1, depth=0.22 if ears == 'fox' else 0.17, location=(s * 0.3, -0.07, hz + 0.41))
            e = bpy.context.object; e.rotation_euler = (0, s * 0.35, 0); e.data.materials.append(im); smooth(e)
    if kind == 'neko':
        sphere((0.2, -0.1, hz + 0.3), (0.2, 0.2, 0.12), mat('nekopatch', '#e8a050', 0.85), 24)
    to2d = sprite_cam(sc, 2.2, 260, 18)
    SPR[kind] = {'res': 260, 'head': to2d((0, -0.3, hz)), 'top': to2d((0, 0, hz + 0.5)), 'base': to2d((0, 0, -0.1))}
    render(sc, kind)

JOBS = {'street': build_street, 'counter': build_counter_layer, 'batter': build_batter}
for k in FISH: JOBS[k] = (lambda k=k: build_fish(k))
for k in ('anko', 'custard', 'matcha'): JOBS[k] = (lambda k=k: build_filling(k))
for k in ANIMALS: JOBS[k] = (lambda k=k: build_animal(k))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
P = lambda x, y, z=0: [round(v, 1) for v in proj(x, y, z)]
meta.update({'pxu': PXU, 'elev': ELEV, 'molds': [P(x, y, IRON_Z) for (x, y) in MOLDS], 'tubs': {k: P(x, y, 0.4) for k, (x, y) in TUBS.items()},
             'counterEdge': P(0, 2.72, 0.12)[1], 'spr': {**meta.get('spr', {}), **SPR}})
json.dump(meta, open(MP, 'w'))
