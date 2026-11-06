# Renders the layers for takoage.html: a winter meadow foreground with the cat holding a string reel (sky left
# transparent; the game paints it), and the kite / kite-bird / balloon sprites (front ortho).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 5.0; TZ = 0.0      # almost level: frame row ~ 640 - z * 160
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
    # clear winter daylight from above-left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 8; a.data.color = srgb('#e0ecff')
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

def tri(pts, y, m):
    me = bpy.data.meshes.new('tri'); me.from_pydata([(x, y, z) for (x, z) in pts], [], [(0, 1, 2)]); o = bpy.data.objects.new('tri', me)
    bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def build_bg():
    sc = reset(True)   # sky stays transparent: the game paints the sky and drifting clouds
    # far snowy mountains, a band of pines, then the meadow hill the cat sits on
    mtn = noise_mat('mtn', '#8aa4c8', '#9ab4d4', 4, 0.95, 0.2); snowc = mat('snowcap', '#f4f8fc', 0.9)
    for (x, r, h) in ((-1.9, 1.5, 0.95), (-0.2, 1.9, 1.25), (1.9, 1.4, 0.8)):
        sphere((x, 14, -2.4), (r, 0.5, h), mtn, 48)
        cap = sphere((x, 13.9, -2.4), (r * 1.01, 0.52, h * 1.01), snowc, 48)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 13.9, -2.4 + h * 1.3)); cut = bpy.context.object; cut.scale = (r * 3, 2, h * 1.0); cut.hide_render = True
        cut.rotation_euler = (0, 0.12 * (1 if x > 0 else -1), 0)
        bo = cap.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'INTERSECT'
    far = noise_mat('far', '#a4c47e', '#b4d090', 6, 0.95, 0.2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -8, -2.35)); o = bpy.context.object; o.scale = (14, 44, 1); o.data.materials.append(far)
    pine = mat('pine', '#3a6a4a', 0.9); pine2 = mat('pine2', '#4a7a52', 0.9); trunk = mat('trunk', '#6a4a30', 0.9)
    random.seed(3)
    for i in range(16):
        x = -2.6 + i * 0.36 + random.uniform(-.1, .1); y = 6 + random.uniform(-.5, .5); hh = random.uniform(0.35, 0.6)
        cyl((x, y, -2.3), 0.03, 0.1, trunk, 8)
        for k in range(3):
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=hh * (0.42 - k * 0.1), depth=hh * 0.5, location=(x, y, -2.2 + k * hh * 0.25))
            o = bpy.context.object; o.data.materials.append(pine if (i + k) % 2 else pine2); smooth(o)
    grass = mat('grass', '#7aa858', 0.85); grass2 = mat('grass2', '#8ab864', 0.85)
    for i in range(60):
        x = random.uniform(-2.4, 2.4); y = random.uniform(-15, -3.5)
        if -2.2 < x < -0.2 and -7.5 < y < -4.5: continue
        z = -2.35
        h = random.uniform(0.1, 0.22)
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.02, depth=h, location=(x, y, z + h / 2)); o = bpy.context.object
        o.rotation_euler = (0, random.uniform(-.4, .4), 0); o.data.materials.append(grass if i % 2 else grass2)
    # the cat sitting on the hilltop facing us, holding the reel up with both paws
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); blk = mat('eye', '#1a1210', 0.9, 0.0)
    pink = mat('nose', '#e88a8a', 0.8); mf = mat('muffler', '#d84a4a', 0.9); mf2 = mat('muffler2', '#f4f0e8', 0.9)
    CX, CZ = -1.25, -2.35 + 0.42
    sphere((CX, -6, CZ), (0.42, 0.34, 0.4), cw, 48)                       # body
    sphere((CX + 0.18, -6.05, CZ + 0.1), (0.2, 0.2, 0.18), co, 32)        # orange patch
    sphere((CX, -6.02, CZ + 0.52), (0.36, 0.3, 0.31), cw, 48)            # head
    sphere((CX - 0.14, -6.12, CZ + 0.66), (0.15, 0.12, 0.11), co, 32)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.12, depth=0.22, location=(CX + s_ * 0.2, -6.02, CZ + 0.84)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.35, 0); e.data.materials.append(co if s_ < 0 else cw); smooth(e)
        sphere((CX + s_ * 0.13, -6.3, CZ + 0.55), (0.04, 0.02, 0.045), blk, 16)  # solid round eyes
        sphere((CX + s_ * 0.17, -6.1, CZ - 0.34), (0.12, 0.1, 0.07), cw, 24)    # feet
    sphere((CX, -6.31, CZ + 0.47), (0.03, 0.02, 0.022), pink, 12)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.27, minor_radius=0.07, location=(CX, -6.0, CZ + 0.27)); o = bpy.context.object; o.scale = (1, 0.9, 0.8); o.data.materials.append(mf); smooth(o)
    # reel (itomaki) held up at the right
    RX, RZ = CX + 0.42, CZ + 0.18
    reelw = wood('reel', '#b07a42', '#c8925a'); thread = mat('thread', '#f4ecd8', 0.9)
    for d in (-0.07, 0.07): disc((RX, -6.3 + d, RZ), 0.16, reelw, 0.03)
    cyl((RX, -6.3, RZ), 0.11, 0.14, thread, 32, rot=(math.radians(90), 0, 0))
    cyl((RX, -6.3, RZ - 0.25), 0.03, 0.3, reelw, 12)
    for s_ in (-1, 1): sphere((RX - 0.05 + s_ * 0.04, -6.42, RZ - 0.16), (0.08, 0.07, 0.07), cw, 24)   # paws on the handle
    tl = None
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.06; tl.data.dimensions = '3D'
    bp = tl.data.splines[0].bezier_points; bp[0].co = (CX - 0.3, -5.8, CZ - 0.28); bp[1].co = (CX - 0.55, -5.9, CZ + 0.02); tl.data.splines[0].bezier_points.add(1); bp = tl.data.splines[0].bezier_points; bp[2].co = (CX - 0.5, -5.95, CZ + 0.3)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    render(sc, 'bg')
    META['reel'] = proj(RX, -6.3, RZ); META['cat'] = proj(CX, -6, CZ + 0.9); META['horizon'] = proj(0, 8, -2.35)[1]

def build_sprites():
    sc = reset(True)   # a square paper kite with a painted cat face and a bamboo cross
    paper = mat('paper', '#fff6e2', 0.9); red = mat('kred', '#e05a4a', 0.9); ora = mat('kora', '#f0a050', 0.9); blk = mat('keye', '#1a1210', 0.9)
    bam = wood('kbam', '#b08a4a', '#c8a060')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (0.9, 0.02, 1.1); o.data.materials.append(paper); bevel(o, 0.008, 2)
    for (x, z, sx, sz) in ((0, 0.52, 0.9, 0.06), (0, -0.52, 0.9, 0.06), (-0.42, 0, 0.06, 1.1), (0.42, 0, 0.06, 1.1)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -0.012, z)); o = bpy.context.object; o.scale = (sx, 0.005, sz); o.data.materials.append(red)
    # painted cat face (flat shapes)
    for s_ in (-1, 1): tri([(s_ * 0.08, 0.2), (s_ * 0.3, 0.16), (s_ * 0.26, 0.42)], -0.014, ora)
    disc((0, -0.014, -0.02), 0.3, ora, 0.004, 64)
    for s_ in (-1, 1): disc((s_ * 0.12, -0.018, 0.02), 0.045, blk, 0.004, 32)
    disc((0, -0.018, -0.07), 0.032, mat('knose', '#e88a8a', 0.9), 0.004, 24)
    for s_ in (-1, 1): disc((s_ * 0.2, -0.017, -0.11), 0.05, mat('kcheek', '#f6c0a0', 0.9), 0.004, 24)
    for a in (math.radians(40), math.radians(-40)): cyl((0, 0.02, 0), 0.012, 1.3, bam, 8, rot=(0, a, 0))
    pt = side_cam(sc, 1.4, 256, 0.0); SPR['kite'] = {'res': 256, 'pxu': 256 / 1.4, 'bridle': pt(0, -0.1), 'tail': pt(0, -0.55)}
    render(sc, 'kite')
    for fr, wa in (('a', 35), ('b', -25)):
        sc = reset(True)   # kite-bird (tonbi) gliding to the right: brown, cream face, round black eye
        br = noise_mat('tb', '#8a5a3a', '#9a6a46', 12, 0.9, 0.2); dk = mat('tbd', '#6a4430', 0.9); cr = mat('tbc', '#f2e2c4', 0.9); be = mat('beak', '#f0b840', 0.6); blk = mat('beye', '#1a1210', 0.9)
        sphere((0, 0, 0), (0.42, 0.2, 0.2), br, 48)
        sphere((0.42, -0.02, 0.06), (0.17, 0.16, 0.15), cr, 32)
        sphere((0.48, -0.15, 0.1), (0.035, 0.02, 0.035), blk, 16)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05, depth=0.13, location=(0.62, -0.02, 0.04), rotation=(0, math.radians(100), 0)); o = bpy.context.object; o.data.materials.append(be); smooth(o)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.2, depth=0.36, location=(-0.5, 0, 0.0), rotation=(0, math.radians(-90), 0)); o = bpy.context.object; o.scale = (0.4, 1, 1); o.data.materials.append(dk); smooth(o)
        w = sphere((-0.04, -0.12, 0.08), (0.24, 0.05, 0.62), br, 40); w.rotation_euler = (0, math.radians(-12), 0)
        w.location = (-0.04 + 0.0, -0.12, 0.08 + 0.55 * math.sin(math.radians(wa)))
        w.scale = (0.24, 0.05, 0.62 * (0.55 + 0.45 * abs(math.sin(math.radians(wa + 55)))))
        sphere((-0.1, -0.13, 0.08 + 0.95 * math.sin(math.radians(wa))), (0.2, 0.04, 0.14), dk, 24)
        side_cam(sc, 1.8, 192, 0.1); SPR['bird'] = {'res': 192, 'pxu': 192 / 1.8}
        render(sc, 'bird_' + fr)
    for name, col in (('red', '#e85a5a'), ('blue', '#5a9ae8'), ('yellow', '#f2c84a'), ('gold', '#e8b030')):
        sc = reset(True)   # matte balloon with a little knot
        m = mat('bl' + name, col, 0.55 if name != 'gold' else 0.3, 0.2 if name != 'gold' else 0.6)
        if name == 'gold': m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.6
        sphere((0, 0, 0.05), (0.3, 0.3, 0.36), m, 48)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05, depth=0.08, location=(0, 0, -0.33)); o = bpy.context.object; o.data.materials.append(m); smooth(o)
        side_cam(sc, 0.9, 128, 0.0); SPR['balloon'] = {'res': 128, 'pxu': 128 / 0.9, 'knot': [64.0, round(64 + 0.37 * 128 / 0.9, 1)]}
        render(sc, 'bal_' + name)

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
