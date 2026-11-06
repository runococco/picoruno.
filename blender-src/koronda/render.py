# Renders the layers for koronda.html: a park ground with a big tree at the far end (camera tilted 35 deg),
# the 'it' cat by the tree (back / turned), and four walking cats seen from behind (walk x2 + frozen pose).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 35.0; TZ = 2.81     # tilted: far ground rises up the frame
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
    # cosy room light from above-front + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.8; s.data.angle = math.radians(15); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 600; a.data.size = 8; a.data.color = srgb('#ffe8d0')
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

def spr_cam(sc, scale, res, tz=0.0):
    p = sprite_cam(sc, scale, res, tz); return p

TRACK = (-1.0, 6.8)   # start y and goal y of the race (world)

def build_bg():
    sc = reset(True)    # sky transparent; game paints it
    sand = noise_mat('sand', '#cdb07a', '#d8bc88', 14, 0.95, 0.25)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, 0)); o = bpy.context.object; o.scale = (14, 30, 1); o.data.materials.append(sand)
    grass = noise_mat('grass', '#78a858', '#88b464', 8, 0.95, 0.3)
    for x in (-3.6, 3.6):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x * 0.8, 6, 0.005)); o = bpy.context.object; o.scale = (1.6, 30, 1); o.data.materials.append(grass)
    # start line
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, TRACK[0], 0.01)); o = bpy.context.object; o.scale = (4.2, 0.08, 1); o.data.materials.append(mat('line', '#fffaf0', 0.9))
    # the big tree at the goal
    bark = noise_mat('bark', '#7a5232', '#8a6040', 20, 0.9, 0.6)
    cyl((0.0, TRACK[1] + 0.9, 1.0), 0.38, 2.0, bark, 32)
    leaf = noise_mat('leaf', '#4a8a4a', '#5a9a52', 6, 0.9, 0.4); leaf2 = noise_mat('leaf2', '#3a7a42', '#4a8a4a', 6, 0.9, 0.4)
    for (x, y, z, r) in ((0, 8.0, 2.6, 1.6), (-1.4, 8.2, 2.1, 1.1), (1.4, 8.2, 2.2, 1.15), (0, 8.4, 3.5, 1.2), (-0.8, 7.9, 3.1, 0.9), (0.9, 7.9, 3.2, 0.9)):
        sphere((x, y, z), (r, r * 0.8, r * 0.85), leaf if x <= 0 else leaf2, 48)
    # hedges and a fence far back, some trees on the sides
    hedge = noise_mat('hedge', '#5a9a52', '#6aaa5a', 10, 0.9, 0.4)
    for x in (-4.2, -2.6, 2.6, 4.2): sphere((x, 8.6, 0.4), (0.9, 0.6, 0.55), hedge, 32)
    fence = wood('fence', '#c8a070', '#d8b080')
    for k in range(17):
        x = -4 + k * 0.5; bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 9.4, 0.6)); o = bpy.context.object; o.scale = (0.1, 0.06, 1.2); o.data.materials.append(fence)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 9.35, 0.9)); o = bpy.context.object; o.scale = (9, 0.05, 0.1); o.data.materials.append(fence)
    for (x, y) in ((-3.4, 3), (3.5, 5), (-3.6, 7), (3.4, 0.5)):
        cyl((x, y, 0.6), 0.14, 1.2, bark, 16); sphere((x, y, 1.6), (0.7, 0.6, 0.75), leaf2 if x > 0 else leaf, 32)
    for (x, y) in ((-2.9, 0.5), (2.9, -0.4), (-3.0, 5.0), (2.8, 6.5)):
        for k in range(3): sphere((x + k * 0.12 - 0.12, y + (k % 2) * 0.08, 0.06), (0.06, 0.06, 0.05), mat('flower' + str(k), ('#f4a0b0', '#fff0a0', '#ffffff')[k], 0.8), 12)
    render(sc, 'bg')
    META['start'] = proj(0, TRACK[0], 0); META['goal'] = proj(0, TRACK[1], 0); META['near'] = proj(1, TRACK[0], 0); META['far'] = proj(1, TRACK[1], 0)
    META['oni'] = proj(0, TRACK[1] + 0.35, 0)

CATS = (('tora', '#f0b060', '#d07a30', 'stripe'), ('shiro', '#fbf6ec', None, 'plain'), ('kuro', '#3e3a40', None, 'plain'), ('saba', '#b8bcc4', '#6a6e78', 'stripe'))

def cat_back(fur, pat, kind, pose):
    """a cat walking away from the camera: back view, tail up; pose = 'a' / 'b' (walk) or 'f' (frozen, one paw up, tail stiff)"""
    fm = mat('f' + fur, fur, 0.85, 0.1, sss=0.15); pm = mat('p' + str(pat), pat, 0.85, 0.1) if pat else fm; inner = mat('inner', '#f0b8b0', 0.85)
    sphere((0, 0, 0.42), (0.32, 0.32, 0.32), fm, 48)                  # body
    sphere((0, 0.24, 0.84), (0.3, 0.26, 0.27), fm, 48)             # head, seen from behind
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.09, depth=0.18, location=(s_ * 0.17, 0.24, 1.1)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.3, 0); e.data.materials.append(fm); smooth(e)
    if kind == 'stripe':
        sphere((0, 0.05, 0.6), (0.22, 0.22, 0.16), pm, 32); sphere((0, 0.2, 1.0), (0.14, 0.12, 0.09), pm, 24)
    ph = {'a': (0.12, -0.12), 'b': (-0.12, 0.12), 'f': (0.0, 0.0)}[pose]
    for i, (lx, ly) in enumerate(((-0.17, 0.18), (0.17, 0.18), (-0.17, -0.18), (0.17, -0.18))):
        sw = ph[(i + (i // 2)) % 2]; up = 0.0
        if pose == 'f' and i == 1: up = 0.22; sw = 0.18
        sphere((lx, ly + sw, 0.14 + up), (0.08, 0.09, 0.15), fm, 24)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.05; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    if pose == 'f': bp[0].co = (0, -0.3, 0.45); bp[1].co = (0.25, -0.45, 0.55); bp[2].co = (0.42, -0.4, 0.8)
    else: bp[0].co = (0, -0.3, 0.45); bp[1].co = (0.1 if pose == 'a' else -0.1, -0.55, 0.8); bp[2].co = (0.22 if pose == 'a' else -0.22, -0.5, 1.0)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(pm if kind == 'stripe' else fm)

def build_cats():
    for name, fur, pat, kind in CATS:
        for pose in ('a', 'b', 'f'):
            sc = reset(True); cat_back(fur, pat, kind, pose)
            pt = spr_cam(sc, 1.6, 192, 0.5); SPR['cat'] = {'res': 192, 'pxu': 120.0, 'foot': pt(0, 0.0)}
            render(sc, f'cat_{name}_{pose}')

def build_oni():
    for pose in ('back', 'front'):
        sc = reset(True)   # the 'it' cat: a big hachiware, paws on the tree (back) or turned around (front)
        fm = mat('of', '#fbf6ec', 0.85, 0.1, sss=0.15); dk = mat('od', '#3a363c', 0.85, 0.1); blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8)
        sphere((0, 0, 0.55), (0.42, 0.36, 0.5), fm, 48)
        hz = 1.15
        sphere((0, 0, hz), (0.36, 0.32, 0.31), fm, 48)
        cap = sphere((0, 0, hz), (0.365, 0.325, 0.315), dk, 48)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, hz + 0.45)); c1 = bpy.context.object; c1.scale = (2, 2, 0.8); c1.hide_render = True
        b1 = cap.modifiers.new('b', 'BOOLEAN'); b1.object = c1; b1.operation = 'INTERSECT'
        if pose == 'front':
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.4, hz + 0.02)); c2 = bpy.context.object; c2.scale = (0.3, 0.6, 0.3); c2.rotation_euler = (0, math.radians(45), 0); c2.hide_render = True
            b2 = cap.modifiers.new('b2', 'BOOLEAN'); b2.object = c2; b2.operation = 'DIFFERENCE'
            for s_ in (-1, 1): sphere((s_ * 0.13, -0.3, hz - 0.02), (0.045, 0.03, 0.05), blk, 16)
            sphere((0, -0.32, hz - 0.1), (0.035, 0.025, 0.025), pink, 12)
            for s_ in (-1, 1): sphere((s_ * 0.3, -0.25, 0.75), (0.1, 0.1, 0.13), fm, 24)     # paws up in surprise
        else:
            for s_ in (-1, 1): sphere((s_ * 0.22, 0.25, 1.05), (0.09, 0.12, 0.09), fm, 24)    # paws covering eyes, on the tree
            bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.06; tl.data.dimensions = '3D'
            bp = tl.data.splines[0].bezier_points; bp[0].co = (0.1, -0.3, 0.35); bp[1].co = (0.4, -0.45, 0.6)
            for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
            tl.data.materials.append(dk)
        for s_ in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.12, depth=0.24, location=(s_ * 0.2, 0, hz + 0.28)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.3, 0); e.data.materials.append(dk); smooth(e)
        pt = spr_cam(sc, 2.0, 240, 0.7); SPR['oni'] = {'res': 240, 'pxu': 120.0, 'foot': pt(0, 0.0)}
        render(sc, 'oni_' + pose)

JOBS = {'bg': build_bg, 'cats': build_cats, 'oni': build_oni}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
