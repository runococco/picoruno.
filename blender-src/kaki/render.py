# Renders the layers for kaki.html: an autumn persimmon tree seen from the front (sky, hills, fence, branches, leaves,
# basket), plus persimmons at four ripeness stages, a splat, a crow (perched / flying), the bamboo picking pole and the
# basket front. python3 render.py <what> <outdir>
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

SLOTS = [(-1.45, 1.55), (-0.85, 2.35), (-0.2, 2.95), (0.55, 2.6), (1.25, 2.05), (1.7, 1.3), (-1.75, 0.65), (-1.0, 1.0),
         (-0.35, 1.75), (0.35, 1.6), (0.95, 1.0), (1.55, 0.35), (-0.6, 0.35), (0.3, 0.6)]

def build_bg():
    sc = reset(False); light(sc); front(sc, 720, 1280)
    sky = bpy.data.materials.new('sky'); sky.use_nodes = True; nt = sky.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    em = nt.nodes.new('ShaderNodeEmission'); tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#fbe2b8'), 1); r.color_ramp.elements[1].color = (*srgb('#8cc4ec'), 1)
    r.color_ramp.elements[0].position = 0.25; nt.links.new(sx.outputs['Y'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (6, 10, 1); o.data.materials.append(sky)
    # far hills and a field
    for hx, hz, sxx, c in ((-1.6, -1.6, 2.6, '#9ab88a'), (1.8, -1.8, 2.4, '#88aa7a'), (0.2, -2.1, 3.2, '#a8c090')):
        sphere((hx, 6, hz), (sxx, 0.4, 1.2), mat('hill' + c, c, 0.95), 48)
    box((0, 4, -3.4), (8, 4, 2.4), noise_mat('field', '#c8b070', '#d6be7e', 6, 0.95, 0.2), 0)
    # low bamboo fence
    bam = mat('fence', '#c8b07a', 0.6); tie = mat('tie', '#6a4a2a', 0.8)
    for i in range(-12, 13): cyl((i * 0.2, 2.0, -2.35), 0.05, 0.9, bam, 12)
    for fz in (-2.15, -2.55): cyl((0, 1.9, fz), 0.04, 5.0, bam, 12, rot=(0, math.radians(90), 0))
    # the tree
    bark = noise_mat('bark', '#5a3e2a', '#6e4e34', 10, 0.9, 0.6)
    branch([(0.1, 0.5, -4.2), (0.0, 0.5, -2.5), (-0.1, 0.5, -1.0), (0.0, 0.5, 0.0)], 0.32, 0.22, bark)
    for pts in ([(0, .5, -.2), (-.8, .5, .5), (-1.5, .5, 1.2), (-1.9, .5, 1.8)], [(0, .5, 0), (.6, .5, .9), (1.2, .5, 1.6), (1.6, .5, 2.4)],
                [(0, .5, 0), (-.2, .5, 1.2), (-.4, .5, 2.3), (-.2, .5, 3.3)], [(-.1, .5, -.6), (-.9, .5, -.2), (-1.7, .5, .3), (-2.3, .5, .4)],
                [(.05, .5, -.4), (.8, .5, -.1), (1.5, .5, .2), (2.2, .5, .1)], [(0, .5, .3), (.5, .5, 1.6), (.7, .5, 2.6), (.5, .5, 3.4)]):
        branch(pts, 0.14, 0.04, bark)
    rnd = random.Random(9)
    can = [noise_mat('cn%d' % i, a_, b_, 3.5, 0.85, 0.5, .3, .75, 8) for i, (a_, b_) in enumerate([('#5e8a3a', '#7aa246'), ('#6e943e', '#a0a848'), ('#86a040', '#c8a042')])]
    for i, (cx, cz, rr) in enumerate(((-1.5, 1.5, .85), (-0.6, 2.55, .95), (0.6, 2.75, .95), (1.4, 1.8, .85), (-1.75, 0.55, .7), (1.7, 0.45, .7),
                                      (0, 1.5, 1.0), (-0.8, 0.9, .75), (0.85, 1.05, .75), (-0.1, 3.3, .6))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, location=(cx, 1.2 + i * 0.05, cz)); o = bpy.context.object
        tx = bpy.data.textures.new('cl%d' % i, 'CLOUDS'); tx.noise_scale = 0.35; d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.22
        e = bpy.data.objects.new('ce%d' % i, None); bpy.context.collection.objects.link(e); e.location = (i * 3.1, i * 1.7, 0); d.texture_coords = 'OBJECT'; d.texture_coords_object = e
        o.scale = (rr, rr * 0.6, rr * 0.82); smooth(o); o.data.materials.append(can[i % 3])
    # basket on the ground
    render(sc, 'bg')
    META['slots'] = [tp(x, z) for x, z in SLOTS]; META['basket'] = tp(0.9, -3.15); META['ground'] = tp(0, -2.9)[1]

def build_basket(front_only):
    sc = reset(True); light(sc); front(sc, 260, 200)
    weave = noise_mat('weave', '#b8884a', '#cc9a58', 30, 0.85, 0.7, .3, .7, 4); rim = mat('brim', '#8a5a2e', 0.7)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.7, depth=0.6, location=(0, 0, -0.1)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        if v.co.z < 0: v.co.x *= 0.78; v.co.y *= 0.78
    tops = [f for f in bm.faces if all(v.co.z > 0.29 for v in f.verts)]; bmesh.ops.delete(bm, geom=tops, context='FACES')
    if front_only: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=True)
    bm.to_mesh(o.data); bm.free(); o.data.materials.append(weave)
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.04
    bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.05, location=(0, 0, 0.2)); t = bpy.context.object; t.data.materials.append(rim)
    if front_only:
        bm = bmesh.new(); bm.from_mesh(t.data); bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=True); bm.to_mesh(t.data); bm.free()
    # tilt the basket a little towards the camera so the opening shows
    for ob in (o, t): ob.rotation_euler.x = math.radians(-18)
    render(sc, 'basketf' if front_only else 'basket')

def kaki(name, base, dark, soft):
    sc = reset(True); light(sc); front(sc, 96, 96)
    m = mat(name, base, 0.35 if not soft else 0.5, 0.35, sss=0.15 if soft else 0)
    o = sphere((0, 0, -0.03), (0.22, 0.22, 0.17 if not soft else 0.15), m, 48)
    if soft: o.scale.x = 0.235
    # four-lobed calyx and stem on top
    cal = mat('cal' + name, dark, 0.7)
    for k in range(4):
        a = k * math.pi / 2 + 0.4; sphere((math.cos(a) * 0.07, math.sin(a) * 0.07 - 0.04, 0.13), (0.085, 0.05, 0.02), cal, 16, rot=(0, 0, a))
    cyl((0, -0.03, 0.17), 0.018, 0.08, mat('stm', '#5a3a22', 0.8), 8)
    render(sc, name)

def build_splat():
    sc = reset(True); light(sc); front(sc, 120, 60, (0, -0.05))
    m = mat('splat', '#e0602a', 0.4, 0.3, sss=0.2)
    sphere((0, 0, -0.12), (0.3, 0.2, 0.06), m, 32)
    for k in range(5): sphere((rnd_.uniform(-.3, .3), 0, -0.13), (0.06, 0.05, 0.03), m, 12)
    render(sc, 'splat')

def build_crow(name, fly):
    sc = reset(True); light(sc); front(sc, 150, 150)
    blk = mat('crow', '#2a2a34', 0.55, 0.3); bk = mat('cbk', '#3a3a40', 0.4); eye = mat('ceye', '#0a0a0a', 0.4)
    sphere((0, 0, 0), (0.24, 0.16, 0.17), blk, 40, rot=(0, math.radians(-15), 0))         # body, facing left (-x)
    sphere((-0.22, 0, 0.12), (0.12, 0.11, 0.11), blk, 32)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.045, depth=0.16, location=(-0.38, 0, 0.11)); o = bpy.context.object; o.rotation_euler = (0, math.radians(-90), 0); o.data.materials.append(bk)
    sphere((-0.26, -0.1, 0.16), (0.022, 0.012, 0.022), eye, 12)
    sphere((0.3, 0, -0.04), (0.16, 0.05, 0.05), blk, 24, rot=(0, math.radians(-20), 0))   # tail
    wa = math.radians(60 if fly else -10)
    o = sphere((0.05, -0.12, 0.05 + (0.15 if fly else 0)), (0.2, 0.03, 0.09), blk, 32, rot=(wa if fly else 0, math.radians(-10), 0))
    if not fly:
        for lx in (-0.04, 0.05): cyl((lx, 0, -0.22), 0.012, 0.14, bk, 8)
    render(sc, name)

def build_pole():
    """long bamboo pole lying along +x, forked tip at the right end; game rotates it from the bottom corner"""
    sc = reset(True); light(sc); front(sc, 1000, 60)
    bam = mat('pole', '#b8a060', 0.4, 0.3); node = mat('pnode', '#988040', 0.5)
    cyl((-0.15, 0, 0), 0.045, 5.6, bam, 16, rot=(0, math.radians(90), 0))
    for k in range(7): cyl((-2.6 + k * 0.8, 0, 0), 0.05, 0.03, node, 16, rot=(0, math.radians(90), 0))
    for s_ in (-1, 1): cyl((2.88, 0, s_ * 0.05), 0.022, 0.26, bam, 10, rot=(0, math.radians(90 - s_ * 20), 0))
    render(sc, 'pole')

rnd_ = random.Random(2)
JOBS = {'bg': build_bg, 'basket': lambda: build_basket(False), 'basketf': lambda: build_basket(True),
        'k0': lambda: kaki('k0', '#8aa83a', '#4a6a2a', False), 'k1': lambda: kaki('k1', '#e8b030', '#4a6a2a', False),
        'k2': lambda: kaki('k2', '#f07a1e', '#4a5a2a', False), 'k3': lambda: kaki('k3', '#d8401e', '#5a4a2a', True),
        'crow0': lambda: build_crow('crow0', False), 'crow1': lambda: build_crow('crow1', True), 'pole': build_pole}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
