# Renders the layers for yukidaruma.html. Full-frame layers share ONE ortho camera (720x1280, 160 px/unit, 58 deg down)
# so the game can stack them; sprites (snowball, hats) use a sprite camera at the same elevation.
# python3 render.py <what> <outdir>      what = all | bg,snow,toro,nanten,ball,bucket,mikan,momiji,twig (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 58.0; TZ = 0.0     # camera: ortho height 8 units looking down at 58 deg, target (0,0,0)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe0f4'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.75
    # low winter morning sun from the upper left, soft sky fill (blue shadows on snow)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(12); s.data.color = srgb('#fff2dc')
    s.rotation_euler = Euler((math.radians(52), math.radians(-28), math.radians(-150)))
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

def holdout(o):
    o.is_holdout = True; return o

# ---------------------------------------------------------------- layout (world units, ground z = 0)
FIELD = (-2.15, 2.15, -4.4, 2.35)            # x0, x1, y0, y1 of the snowy garden
POND = (0.95, -1.05, 0.78, 0.55)             # cx, cy, rx, ry (frozen pond, no snow)
TORO = (-1.5, 0.95)                          # stone lantern
NANTEN = (1.55, -3.15)                       # nandina bush with red berries
PINE = (1.6, 1.75)                           # small round pine
ROCKS = [(-0.75, -2.25, 0.2), (-1.65, -3.6, 0.17), (0.3, 1.35, 0.15), (-0.2, -0.6, 0.13)]
STONES = [(0.15, 2.0), (-0.1, 1.45), (0.1, 0.9), (-0.15, 0.3), (0.0, -0.3), (-0.3, -0.95), (-0.15, -1.6), (0.15, -2.3), (0.35, -3.0), (0.2, -3.7)]

def ground_objects():
    soil = noise_mat('soil', '#5a4632', '#6e5a3e', 9, 0.95, 0.5)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -1, 0)); g = bpy.context.object; g.scale = (6, 9, 1); g.data.materials.append(soil)
    grass = noise_mat('wgrass', '#8a8a4a', '#a89a5a', 14, 0.95, 0.6, 0.45, 0.62)
    random.seed(2)
    for k in range(70):   # tufts of winter grass
        x = random.uniform(-2.2, 2.2); y = random.uniform(-4.6, 2.3)
        if (x - POND[0]) ** 2 / POND[2] ** 2 + (y - POND[1]) ** 2 / POND[3] ** 2 < 1.4: continue
        sphere((x, y, 0), (random.uniform(.12, .26), random.uniform(.1, .2), .04), grass, 12)
    st = noise_mat('stepstone', '#8a8478', '#a29c90', 7, 0.8, 0.4)
    for (x, y) in STONES:
        o = cyl((x, y, 0.02), 0.26, 0.06, st, 32); o.scale = (1.0, 0.82, 1); bevel(o, 0.02)
    # frozen pond: ice disc in a ring of stones
    ice = mat('ice', '#a8d0e8', 0.08, 0.6)
    o = cyl((POND[0], POND[1], 0.005), 1, 0.02, ice, 64); o.scale = (POND[2], POND[3], 1)
    rim = noise_mat('rimstone', '#7a746a', '#948e84', 8, 0.85, 0.5)
    for k in range(18):
        a = k / 18 * math.tau
        sphere((POND[0] + math.cos(a) * (POND[2] + .07), POND[1] + math.sin(a) * (POND[3] + .07), 0.02), (.12, .1, .07), rim, 16, (0, 0, a))

def build_bg():
    sc = reset(False)
    ground_objects()
    # engawa (veranda) across the top with a sleeping cat on a cushion
    wd = wood('engawa', '#a8764a', '#8a5a36')
    for k in range(9):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.62 + k * 0.22, 0.42)); b = bpy.context.object; b.scale = (6, 0.21, 0.06); b.data.materials.append(wd); bevel(b, 0.01)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.52, 0.2)); f = bpy.context.object; f.scale = (6, 0.06, 0.42); f.data.materials.append(wood('engawa2', '#7a5434', '#6a4628'))
    sh = mat('shoji', '#f8f2e4', 0.9, 0.05); fr = mat('shojifr', '#b8946a', 0.6, 0.1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.6, 1.4)); w = bpy.context.object; w.scale = (6, 0.05, 2); w.data.materials.append(sh)
    for k in range(-6, 7):
        cyl((k * 0.42, 4.55, 1.4), 0.018, 2.0, fr, 8)
    # zabuton + cat
    zb = noise_mat('zabuton', '#6a5aa0', '#7a6ab0', 20, 0.9, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.15, 3.35, 0.5)); z = bpy.context.object; z.scale = (0.9, 0.8, 0.08); z.data.materials.append(zb); bevel(z, 0.04, 6)
    cat(1.15, 3.35, 0.56)
    # snow piled on the engawa edge
    snow = snow_mat()
    for k in range(14):
        sphere((-3 + k * 0.46, 2.56, 0.46), (0.3, 0.12, 0.05), snow, 16)
    render(sc, 'bg')

def cat(cx, cy, cz):
    wh = mat('catw', '#fbf6ec', 0.8, 0.1, sss=0.2); og = mat('cato', '#e8a050', 0.8, 0.1); bk = mat('catb', '#3a2c24', 0.8, 0.1)
    body = sphere((cx, cy, cz + 0.16), (0.36, 0.3, 0.18), wh, 32)
    sphere((cx - 0.12, cy + 0.08, cz + 0.28), (0.16, 0.14, 0.08), og, 24)      # orange patch
    sphere((cx + 0.16, cy - 0.06, cz + 0.27), (0.12, 0.1, 0.07), bk, 24)       # black patch
    hx, hy = cx - 0.3, cy - 0.12
    sphere((hx, hy, cz + 0.2), (0.17, 0.16, 0.14), wh, 32)
    sphere((hx + 0.04, hy + 0.06, cz + 0.3), (0.09, 0.08, 0.05), og, 16)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.06, depth=0.11, location=(hx + s * 0.08, hy + 0.06, cz + 0.33))
        e = bpy.context.object; e.rotation_euler = (math.radians(-20), s * math.radians(20), 0); e.data.materials.append(og if s < 0 else wh)
    ink = mat('ink', '#4a2c1d', 0.6, 0.1)
    for s in (-1, 1):   # closed sleeping eyes: tiny arcs
        pts = [(hx + s * 0.065 + math.cos(a) * 0.035, hy - 0.135, cz + 0.255 - math.sin(a) * 0.022) for a in (0.2, 1.0, 1.57, 2.14, 2.94)]
        cu = bpy.data.curves.new('eye', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 3
        for j, p in enumerate(pts): sp.points[j].co = (*p, 1)
        ob = bpy.data.objects.new('eye', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(ink)
    tail = [(cx + 0.3, cy + 0.05, cz + 0.08), (cx + 0.2, cy - 0.28, cz + 0.06), (cx - 0.1, cy - 0.32, cz + 0.06), (hx + 0.05, hy - 0.2, cz + 0.08)]
    cu = bpy.data.curves.new('tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.045; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(tail) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for j, p in enumerate(tail): sp.points[j].co = (*p, 1)
    ob = bpy.data.objects.new('tail', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(og)

def snow_mat():
    m = bpy.data.materials.get('snow')
    if m: return m
    m = noise_mat('snow', '#e8eef8', '#ffffff', 5, 0.9, 0.25, 0.3, 0.75)
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (0.6, 0.7, 0.9); b.inputs['Subsurface Scale'].default_value = 0.05
    return m

def build_snow():
    sc = reset(True)
    x0, x1, y0, y1 = FIELD
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=240, size=1, location=((x0 + x1) / 2, (y0 + y1) / 2 - 0.3, 0.06))
    g = bpy.context.object; g.scale = (x1 - x0 + 0.5, y1 - y0 + 0.6, 1); bpy.ops.object.transform_apply(scale=True)
    random.seed(5)
    for v in g.data.vertices:   # soft drifts, a little thinner near the engawa
        x, y = v.co.x + g.location.x, v.co.y + g.location.y
        v.co.z = 0.035 * math.sin(x * 2.3 + 1) * math.sin(y * 1.7) + 0.02 * math.sin(x * 5.1 + y * 3.3) + 0.012 * random.random()
    smooth(g); g.data.materials.append(snow_mat())
    # the frozen pond has no snow, the tall props stand on bare spots
    o = cyl((POND[0], POND[1], 0.05), 1, 0.3, mat('x', '#000000'), 64); o.scale = (POND[2] + 0.02, POND[3] + 0.02, 1); holdout(o)
    render(sc, 'snow')

def build_rocks():
    sc = reset(True)
    rk = noise_mat('rock', '#6a665e', '#8a847a', 6, 0.85, 0.6); sn = snow_mat()
    for (x, y, r) in ROCKS:
        o = sphere((x, y, r * 0.35), (r, r * 0.85, r * 0.75), rk, 32, (0, 0, random.random()))
        sphere((x - r * 0.1, y + r * 0.05, r * 0.8), (r * 0.75, r * 0.6, r * 0.28), sn, 24)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -1, 0.0)); g = bpy.context.object; g.scale = (8, 12, 1); holdout(g)
    render(sc, 'rocks')

def build_toro():
    sc = reset(True)
    x, y = TORO; st = noise_mat('torostone', '#8c887e', '#a8a296', 8, 0.85, 0.5); sn = snow_mat()
    cyl((x, y, 0.06), 0.24, 0.12, st, 6)
    cyl((x, y, 0.4), 0.08, 0.6, st, 24)
    cyl((x, y, 0.74), 0.22, 0.1, st, 6)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.92)); fb = bpy.context.object; fb.scale = (0.26, 0.26, 0.26); fb.data.materials.append(st)
    win = mat('torowin', '#ffd890', 0.5, 0.1, emit=('#ffc860', 0.6))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 0.13, 0.92)); w = bpy.context.object; w.scale = (0.14, 0.02, 0.13); w.data.materials.append(win)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.38, radius2=0.04, depth=0.26, location=(x, y, 1.18)); r = bpy.context.object; r.data.materials.append(st)
    sphere((x, y, 1.3), (0.06, 0.06, 0.06), st, 16)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.36, radius2=0.08, depth=0.16, location=(x, y, 1.24)); s = bpy.context.object; s.data.materials.append(sn); smooth(s)
    sphere((x, y, 1.04 + 0.1), (0.2, 0.2, 0.04), sn, 16)
    sphere((x, y, 0.8), (0.2, 0.2, 0.04), sn, 16)
    sphere((x, y, 0.13), (0.27, 0.27, 0.04), sn, 16)
    render(sc, 'toro')

def build_nanten(name='nanten', at=NANTEN):
    sc = reset(True)
    x, y = at; lf = noise_mat('nantenleaf', '#4a6a2a', '#7a5a2a', 5, 0.6, 0.3); br = mat('berry', '#d83a2a', 0.3, 0.5); sn = snow_mat()
    stem = mat('nstem', '#6a4a2a', 0.8)
    random.seed(9)
    for k in range(7):
        a = k / 7 * math.tau; h = 0.7 + random.random() * 0.25
        cyl((x + math.cos(a) * .06, y + math.sin(a) * .06, h / 2), 0.015, h, stem, 6)
        for j in range(5):
            sphere((x + math.cos(a + j) * .2 * random.random(), y + math.sin(a + j) * .2 * random.random(), h * (0.4 + j * 0.13)), (.16, .06, .03), lf, 8, (random.random(), random.random(), random.random() * 3))
    for k in range(4):   # berry clusters
        cx, cy, cz = x + random.uniform(-.2, .2), y - 0.15 + random.uniform(-.1, .05), 0.75 + random.uniform(0, .2)
        for j in range(9): sphere((cx + random.uniform(-.07, .07), cy + random.uniform(-.05, .05), cz + random.uniform(-.06, .04)), (.035, .035, .035), br, 12)
    for k in range(5): sphere((x + random.uniform(-.2, .2), y + random.uniform(-.15, .15), 0.95 + random.uniform(0, .1)), (.14, .12, .04), sn, 12)
    sphere((x, y, 0.03), (.3, .26, .05), sn, 16)
    render(sc, name)

def build_pine():
    sc = reset(True)
    x, y = PINE; nd = noise_mat('needle', '#2e5a32', '#4a7a40', 18, 0.8, 0.6); sn = snow_mat(); bark = mat('pinebark', '#5a3a28', 0.9)
    cyl((x, y, 0.3), 0.06, 0.6, bark, 12)
    for (dx, dy, z, r) in ((0, 0, .65, .42), (-.18, .05, .95, .3), (.15, -.04, 1.05, .28), (0, .02, 1.3, .24)):
        sphere((x + dx, y + dy, z), (r, r * .9, r * .45), nd, 24)
        sphere((x + dx - .02, y + dy + .02, z + r * .32), (r * .85, r * .75, r * .2), sn, 24)
    render(sc, 'pine')

# ---------------------------------------------------------------- sprites (sprite camera at the same 58 deg elevation)
SPR = {}
def sprite_cam(sc, scale, res, elev=ELEV):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(elev); d = 30; loc = Vector((0, -math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (-loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    m = c.matrix_world.to_3x3()
    return lambda p: (res / 2 + Vector(p).dot(m.col[0]) * res / scale, res / 2 - Vector(p).dot(m.col[1]) * res / scale)

def build_ball():
    sc = reset(True)
    o = sphere((0, 0, 0), (1, 1, 1), snow_mat(), 64)
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('lumps', 'CLOUDS'); tx.noise_scale = 0.35; d.texture = tx; d.strength = 0.05
    sprite_cam(sc, 2.3, 256)
    SPR['ball'] = {'res': 256, 'scale': 2.3}
    render(sc, 'ball')

def build_bucket():
    sc = reset(True)
    rd = mat('bucket', '#d84a3a', 0.35, 0.5); rim = mat('bucketrim', '#b8b8c0', 0.3, 0.7)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.42, radius2=0.3, depth=0.58, location=(0, 0, 0.29)); b = bpy.context.object; b.data.materials.append(rd); smooth(b); bevel(b, 0.02)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.025, location=(0, 0, 0.0)); bpy.context.object.data.materials.append(rim)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.02, location=(0, 0, 0.58)); bpy.context.object.data.materials.append(rim)
    to2d = sprite_cam(sc, 1.3, 200); SPR['bucket'] = {'res': 200, 'scale': 1.3, 'base': to2d((0, 0, 0))}
    render(sc, 'bucket')

def build_mikan():
    sc = reset(True)
    mk = noise_mat('mikan', '#f08a1e', '#f8a032', 40, 0.5, 0.4); lf = mat('mleaf', '#4a7a2a', 0.5, 0.3); st = mat('mstem', '#5a4a2a', 0.7)
    sphere((0, 0, 0.26), (0.34, 0.34, 0.27), mk, 48)
    cyl((0, 0, 0.54), 0.03, 0.06, st, 8)
    sphere((0.12, 0.02, 0.56), (0.16, 0.06, 0.02), lf, 16, (0, math.radians(-15), 0.3))
    to2d = sprite_cam(sc, 1.0, 180); SPR['mikan'] = {'res': 180, 'scale': 1.0, 'base': to2d((0, 0, 0))}
    render(sc, 'mikan')

def build_momiji():
    sc = reset(True)
    lf = noise_mat('momiji', '#d8381e', '#e86a2a', 6, 0.6, 0.2)
    pts = []
    for k in range(5):   # five-lobed maple leaf as a flat mesh
        a = math.radians(90 + (k - 2) * 50); L = 0.42 if k == 2 else (0.36 if k in (1, 3) else 0.26)
        pts += [(math.cos(a - .28) * L * .35, math.sin(a - .28) * L * .35), (math.cos(a) * L, math.sin(a) * L)]
    me = bpy.data.meshes.new('m'); bm = bmesh.new(); c0 = bm.verts.new((0, 0, 0)); vs = [bm.verts.new((x, y, 0)) for x, y in pts]
    for k in range(len(vs)): bm.faces.new((c0, vs[k], vs[(k + 1) % len(vs)]))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('m', me); bpy.context.collection.objects.link(o); o.data.materials.append(lf)
    s = o.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.02
    o.rotation_euler = (math.radians(-20), 0, math.radians(-15)); o.location = (0, 0, 0.1)
    cyl((0, -0.12, 0.06), 0.012, 0.18, mat('mst', '#8a3a1a', 0.7), 6, (math.radians(70), 0, 0))
    to2d = sprite_cam(sc, 1.1, 180); SPR['momiji'] = {'res': 180, 'scale': 1.1, 'base': to2d((0, 0, 0))}
    render(sc, 'momiji')

def build_twig():
    sc = reset(True)
    br = mat('twig', '#5a3a26', 0.85)
    def seg(pts, r):
        cu = bpy.data.curves.new('t', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = min(3, len(pts))
        for j, p in enumerate(pts): sp.points[j].co = (*p, 1); sp.points[j].radius = 1 - 0.6 * j / (len(pts) - 1)
        ob = bpy.data.objects.new('t', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(br)
    seg([(0, 0, 0), (0.3, 0, 0.08), (0.62, 0, 0.2)], 0.045)        # arm pointing +x, slightly up
    seg([(0.38, 0, 0.1), (0.5, 0, 0.3), (0.56, 0, 0.4)], 0.028)
    seg([(0.55, 0, 0.18), (0.72, 0, 0.17)], 0.022)
    to2d = sprite_cam(sc, 1.6, 200); SPR['twig'] = {'res': 200, 'scale': 1.6, 'base': to2d((0, 0, 0))}
    render(sc, 'twig')

JOBS = {'bg': build_bg, 'snow': build_snow, 'rocks': build_rocks, 'toro': build_toro, 'nanten': build_nanten, 'pine': build_pine,
        'ball': build_ball, 'bucket': build_bucket, 'mikan': build_mikan, 'momiji': build_momiji, 'twig': build_twig}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
P = lambda x, y, z=0: [round(v, 1) for v in proj(x, y, z)]
meta.update({'pxu': PXU, 'elev': ELEV, 'field': FIELD,
             'pond': [*P(POND[0], POND[1]), POND[2] * PXU, POND[3] * PXU],
             'props': {'toro': [*P(*TORO), 0.27 * PXU], 'nanten': [*P(*NANTEN), 0.3 * PXU], 'pine': [*P(*PINE), 0.42 * PXU]},
             'rocks': [[*P(x, y), r * PXU] for (x, y, r) in ROCKS],
             'spr': {**meta.get('spr', {}), **SPR}})
json.dump(meta, open(MP, 'w'))
