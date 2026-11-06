# Renders the layers for senko.html: a summer-night veranda seen from the side with the cat sitting on it (sky left
# transparent; the game paints the stars), plus the paw that holds the sparkler and the wind-bell sprite (side ortho).
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#4a5a9a'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    # soft moonlight from above-left, a warm glow from the right (the sparkler side) and a blue fill from the front
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.4; s.data.angle = math.radians(25); s.data.color = srgb('#c8d4ff')
    s.rotation_euler = Euler((math.radians(30), math.radians(-25), math.radians(0)))
    bpy.ops.object.light_add(type='POINT', location=(1.2, -2.5, -0.6))
    p = bpy.context.object; p.data.energy = 900; p.data.shadow_soft_size = 1.2; p.data.color = srgb('#ffb060')
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 420; a.data.size = 8; a.data.color = srgb('#b8c8ff')
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

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    """a slightly larger copy of a body sphere, cut to the cutter: a flush colour patch"""
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o

CAT = (-1.15, -1.0, -1.55)
def build_bg():
    sc = reset(True)
    board = wood('board', '#8a6038', '#a07448'); dark = wood('edge', '#5a3a22', '#6a4628')
    # engawa: boards seen end-on, the front beam, posts and the eave at the top
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.5, -2.15)); o = bpy.context.object; o.scale = (9, 4.5, 0.2); o.data.materials.append(board); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.75, -2.45)); o = bpy.context.object; o.scale = (9, 0.2, 0.5); o.data.materials.append(dark); bevel(o, 0.02, 2)
    for x in (-1.9,):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -1.4, 0.6)); o = bpy.context.object; o.scale = (0.22, 0.22, 5.6); o.data.materials.append(dark); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.2, 3.55)); o = bpy.context.object; o.scale = (9, 1.6, 0.18); o.data.materials.append(dark); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.95, 3.35)); o = bpy.context.object; o.scale = (9, 0.12, 0.3); o.data.materials.append(board); bevel(o, 0.02, 2)
    # the garden: dark lawn, a hedge, a stone and a little water bucket
    lawn = noise_mat('lawn', '#24402a', '#2e5232', 8, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2, -3.0)); o = bpy.context.object; o.scale = (12, 14, 1); o.data.materials.append(lawn)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.0, -2.9)); o = bpy.context.object; o.scale = (12, 3.6, 0.2); o.data.materials.append(lawn)
    hedge = noise_mat('hedge', '#1e3a26', '#2a4a30', 9, 0.95, 0.6)
    for k in range(7):
        sphere((-2.6 + k * 0.85, 7.5, -1.6 + (k % 2) * 0.15), (0.75, 0.5, 0.65), hedge, 32)
    stone = noise_mat('stone', '#6a6e78', '#888c96', 7, 0.9, 0.4)
    sphere((1.5, -2.6, -2.95), (0.38, 0.3, 0.16), stone, 32)
    pail = mat('pail', '#4a7ab8', 0.5, 0.3); water = mat('water', '#8ab8e8', 0.15, 0.5)
    cyl((1.45, -2.65, -2.62), 0.24, 0.42, pail, 48); cyl((1.45, -2.65, -2.42), 0.215, 0.02, water, 48)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.02, location=(1.45, -2.65, -2.41)); o = bpy.context.object; o.data.materials.append(pail)
    # the cat, side view facing right, sitting on the boards; its right paw is the game's sprite
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#4a4248', 0.85, 0.1)
    blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8); inner = mat('inner', '#f0b8b0', 0.85)
    X, Y, Z = CAT; before = set(bpy.data.objects)
    bs = (0.52, 0.44, 0.5); sphere((X, Y, Z), bs, cw, 64)
    paint_on((X, Y, Z), bs, co, (X - 0.45, Y - 0.2, Z + 0.25), (0.42, 0.6, 0.38))
    hl = (X + 0.18, Y - 0.02, Z + 0.68); hs = (0.38, 0.34, 0.33); sphere(hl, hs, cw, 64)
    paint_on(hl, hs, cg, (hl[0] - 0.3, hl[1] - 0.1, hl[2] + 0.28), (0.36, 0.5, 0.3))
    for s_, m in ((-1, cg), (1, co)):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.12, depth=0.24, location=(hl[0] + 0.02 + s_ * 0.0, hl[1] + s_ * 0.18, hl[2] + 0.32)); e = bpy.context.object; e.rotation_euler = (s_ * -0.35, 0.1, 0); e.data.materials.append(m); smooth(e)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.07, depth=0.12, location=(hl[0] + 0.05, hl[1] - 0.2, hl[2] + 0.3)); e = bpy.context.object; e.rotation_euler = (0.35, 0.1, 0); e.scale = (1, 0.3, 1); e.data.materials.append(inner); smooth(e)
    # eye and nose on the right side of the face, looking up at the sparkler
    sphere((hl[0] + 0.3, hl[1] - 0.18, hl[2] + 0.06), (0.045, 0.03, 0.06), blk, 24)
    sphere((hl[0] + 0.375, hl[1] - 0.05, hl[2] - 0.06), (0.03, 0.03, 0.022), pink, 16)
    sphere((hl[0] + 0.33, hl[1] - 0.06, hl[2] - 0.13), (0.07, 0.11, 0.06), cw, 24)
    # back leg and tail curled on the boards
    sphere((X - 0.05, Y - 0.22, Z - 0.38), (0.3, 0.14, 0.14), cw, 32)
    sphere((X + 0.32, Y - 0.2, Z - 0.44), (0.15, 0.1, 0.07), cw, 24)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.075; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    bp[0].co = (X - 0.4, Y + 0.05, Z - 0.35); bp[1].co = (X - 0.75, Y - 0.15, Z - 0.42); bp[2].co = (X - 0.85, Y - 0.35, Z - 0.1)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    K = 1.35; P = Vector((X, Y, Z - 0.5))   # scale the whole cat up about where it sits
    for o in set(bpy.data.objects) - before:
        o.location = P + (o.location - P) * K; o.scale = o.scale * K
        if o.type == 'CURVE':
            for b in o.data.splines[0].bezier_points: b.co = P + (b.co - P) * K; b.handle_left = P + (b.handle_left - P) * K; b.handle_right = P + (b.handle_right - P) * K
            o.scale = (1, 1, 1); o.data.bevel_depth *= K
    render(sc, 'bg')
    sh = P + (Vector((X + 0.28, Y - 0.3, Z + 0.22)) - P) * K
    META['shoulder'] = proj(*sh); META['eave'] = proj(0, -1.95, 3.2)[1]; META['ground'] = proj(0, -2.6, -3.0)[1]
    META['boards'] = proj(0, -1.6, -2.05)[1]; META['pail'] = proj(1.45, -2.65, -2.42)

def build_paw():
    sc = reset(True)
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); pink = mat('pad', '#f0a8a8', 0.8)
    sphere((0, 0, 0), (0.2, 0.17, 0.17), cw, 48)
    for k in range(3): sphere((0.12 + 0.02 * (k == 1), -0.1 + k * 0.1, 0.09), (0.06, 0.05, 0.05), cw, 24)
    side_cam(sc, 0.6, 96, 0.0); SPR['paw'] = {'res': 96, 'pxu': 160.0}
    render(sc, 'paw')

def build_furin():
    sc = reset(True)   # a glass wind bell with a painted goldfish, hanging by a string; the paper strip is drawn by the game
    glass = mat('glass', '#e8f4ff', 0.25, 0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, 0, 0)); o = bpy.context.object; o.scale = (0.32, 0.32, 0.3); smooth(o); o.data.materials.append(glass)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.32)); c = bpy.context.object; c.scale = (1, 1, 0.5); c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'DIFFERENCE'
    red = mat('fish', '#e0504a', 0.7); blue = mat('wave', '#5a8ad8', 0.7)
    for k in range(3):
        a = -0.6 + k * 0.6; sphere((math.sin(a) * 0.3, -math.cos(a) * 0.3 + 0.02, -0.08 + 0.04 * (k % 2)), (0.06, 0.02, 0.035), red, 16, rot=(0, 0.2, a))
    paint_on((0, 0, 0), (0.32, 0.32, 0.3), blue, (0, -0.3, -0.18), (0.6, 0.6, 0.05))
    cyl((0, 0, 0.32), 0.035, 0.06, mat('knob', '#c89850', 0.5), 16)
    side_cam(sc, 1.0, 128, -0.05); SPR['furin'] = {'res': 128, 'pxu': 128.0, 'top': 64 - 0.35 * 128 + 0.05 * 128, 'mouth': 64 + 0.05 * 128}
    render(sc, 'furin')

JOBS = {'bg': build_bg, 'paw': build_paw, 'furin': build_furin}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
