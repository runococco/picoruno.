# Renders the layers for otedama.html: a tatami room with the cat sitting on a cushion (paws drawn by the game),
# and the paw / beanbag sprites (front ortho).
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff2e0'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # warm room light from above-left + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(20); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 8; a.data.color = srgb('#ffe8d0')
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
    sc = reset(False)
    # back wall: shoji panels between wooden posts, a plaster band above; tatami floor
    plaster = noise_mat('plaster', '#efe2c8', '#f6ead4', 8, 0.95, 0.15)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 4, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (8, 12, 1); o.data.materials.append(plaster)
    paper = mat('shoji', '#fbf6ea', 0.95); paper.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (*srgb('#fff4dc'), 1); paper.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.35
    frame = wood('frame', '#a87a4a', '#b88a58'); post = wood('post', '#8a5e36', '#9a6c40')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 3.95, 0.4), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (4.0, 4.2, 1); o.data.materials.append(paper)
    for i in range(9):
        x = -2.0 + i * 0.5; bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 3.9, 0.4)); o = bpy.context.object; o.scale = (0.035 if i % 4 else 0.08, 0.04, 4.2); o.data.materials.append(frame)
    for k in range(8):
        z = -1.7 + k * 0.55; bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.9, z)); o = bpy.context.object; o.scale = (4.0, 0.04, 0.035); o.data.materials.append(frame)
    for x in (-2.15, 2.15): bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 3.85, 0)); o = bpy.context.object; o.scale = (0.22, 0.22, 9); o.data.materials.append(post); bevel(o, 0.02)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.85, 2.6)); o = bpy.context.object; o.scale = (6, 0.2, 0.16); o.data.materials.append(post)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3.85, -1.85)); o = bpy.context.object; o.scale = (6, 0.25, 0.14); o.data.materials.append(post)
    tat = noise_mat('tatami', '#c8c088', '#d4cc96', 40, 0.9, 0.3, detail=2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -24, -1.92)); o = bpy.context.object; o.scale = (8, 56, 1); o.data.materials.append(tat)
    edge = mat('heri', '#3a4a5a', 0.9)
    for y in (-0.6, -6.6, -12.6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, -1.915)); o = bpy.context.object; o.scale = (8, 0.12, 0.01); o.data.materials.append(edge)
    # zabuton
    zb = noise_mat('zabuton', '#8a5aa8', '#9a68b8', 30, 0.9, 0.2, detail=2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.2, -1.82)); o = bpy.context.object; o.scale = (2.3, 2.0, 0.22); o.data.materials.append(zb); bevel(o, 0.09, 6)
    # the cat sitting, facing us (paws raised are drawn by the game)
    before = set(bpy.data.objects)
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#5a5258', 0.85, 0.1); blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8)
    CY = -2.2; BZ = -1.15
    sphere((0, CY, BZ), (0.62, 0.5, 0.62), cw, 64)                         # body
    sphere((0.26, CY - 0.05, BZ + 0.15), (0.3, 0.3, 0.3), co, 32)
    sphere((-0.3, CY + 0.05, BZ - 0.25), (0.26, 0.3, 0.24), cg, 32)
    HZ = BZ + 0.86
    sphere((0, CY - 0.05, HZ), (0.52, 0.42, 0.44), cw, 64)                 # head
    sphere((0.2, CY - 0.18, HZ + 0.2), (0.22, 0.16, 0.16), co, 32)
    sphere((-0.22, CY - 0.16, HZ + 0.18), (0.2, 0.15, 0.15), cg, 32)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.17, depth=0.3, location=(s_ * 0.3, CY - 0.05, HZ + 0.4)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.38, 0); e.data.materials.append(co if s_ > 0 else cg); smooth(e)
        sphere((s_ * 0.18, CY - 0.45, HZ + 0.02), (0.055, 0.03, 0.06), blk, 16)
        sphere((s_ * 0.24, CY - 0.2, BZ - 0.55), (0.17, 0.14, 0.09), cw, 24)   # hind feet
    sphere((0, CY - 0.47, HZ - 0.08), (0.04, 0.025, 0.03), pink, 12)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.07; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    bp[0].co = (0.5, CY + 0.2, BZ - 0.5); bp[1].co = (0.95, CY - 0.1, BZ - 0.45); bp[2].co = (1.05, CY - 0.3, BZ - 0.1)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    K = 1.45; piv = Vector((0, CY, -1.92))
    for o in set(bpy.data.objects) - before:
        o.location = piv + (o.location - piv) * K; o.scale = o.scale * K
    sk = lambda x, y, z: tuple(piv + (Vector((x, y, z)) - piv) * K)
    render(sc, 'bg')
    for s_, k in ((-1, 'shL'), (1, 'shR')): META[k] = proj(*sk(s_ * 0.5, CY - 0.1, BZ + 0.3))
    META['head'] = proj(*sk(0, CY, HZ)); META['eyes'] = [proj(*sk(s_ * 0.18, CY - 0.45, HZ + 0.02)) for s_ in (-1, 1)]; META['floor'] = proj(0, -2.2, -1.92)[1]

def build_sprites():
    sc = reset(True)   # a raised front paw seen from the front: round, three toe grooves
    cw = mat('pw', '#fbf6ec', 0.85, 0.1, sss=0.2); groove = mat('pg', '#d8cfc0', 0.9)
    sphere((0, 0, 0), (0.2, 0.16, 0.22), cw, 48)
    for dx in (-0.06, 0.06): cyl((dx, -0.155, 0.1), 0.008, 0.12, groove, 8)
    side_cam(sc, 0.6, 96, 0.0); SPR['paw'] = {'res': 96, 'pxu': 160.0}
    render(sc, 'paw')
    for name, c1, c2 in (('aka', '#d84a4a', '#f2a0a0'), ('ai', '#3a6ab8', '#a0c0f0'), ('kiku', '#e8b030', '#fff0b0'), ('wakaba', '#5aa85a', '#c0e8a0')):
        sc = reset(True)   # a beanbag: soft pillow of patterned chirimen cloth
        m = bpy.data.materials.new('bag' + name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9
        nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = 'CONSTANT'
        r.color_ramp.elements[0].position = 0.0; r.color_ramp.elements[1].position = 0.12
        r.color_ramp.elements[0].color = (*srgb(c2), 1); r.color_ramp.elements[1].color = (*srgb(c1), 1)
        nt.links.new(vo.outputs['Distance'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.95; b.inputs['Specular IOR Level'].default_value = 0.08
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (0.32, 0.26, 0.26)
        sub = o.modifiers.new('s', 'SUBSURF'); sub.levels = 3; sub.render_levels = 3
        o.rotation_euler = (math.radians(15), math.radians(20), math.radians(25)); o.data.materials.append(m); smooth(o)
        side_cam(sc, 0.6, 96, 0.0); SPR['bag'] = {'res': 96, 'pxu': 160.0}
        render(sc, 'bag_' + name)

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
