# Renders the layers for yajirobe.html: a study desk by a window (side view), the pencil the toy balances on,
# the wooden balancing toy (a little bird with two long arms) and the small things that get piled on its arms.
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
    # warm afternoon light from above-left + sky fill
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

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o

DESK = -2.6
def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#f4ead8'), 1)
    wall = noise_mat('wall', '#f2e6d0', '#f6ecdc', 10, 0.95, 0.05)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 4, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (14, 16, 1); o.data.materials.append(wall); o.visible_diffuse = False
    # window with sky and a curtain at the top left
    sky = mat('sky', '#a8d8f4', 0.9, 0.0, emit=('#bfe4f8', 0.8)); frame = wood('wframe', '#c8a070', '#d6b080')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.6, 3.95, 2.3), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (3.4, 2.6, 1); o.data.materials.append(sky)
    for (x, z, w, h) in ((-0.6, 3.6, 3.84, 0.14), (-0.6, 1.0, 3.84, 0.14), (-2.35, 2.3, 0.12, 2.7), (1.15, 2.3, 0.12, 2.7), (-0.6, 2.3, 0.08, 2.6)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 3.9 if w > 1 else 3.885, z)); o = bpy.context.object; o.scale = (w, 0.1 if w > 1 else 0.12, h if w > 1 else h - 0.15); o.data.materials.append(frame)
    cur = noise_mat('curtain', '#f2c8a0', '#f6d4b0', 6, 0.95, 0.3)
    for k in range(5): cyl((1.6 + k * 0.18, 3.7, 2.3), 0.12, 2.9, cur, 24)
    # desk top and front edge
    desk = wood('desk', '#b07c50', '#c08c5e')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.2, DESK - 0.15)); o = bpy.context.object; o.scale = (14, 5, 0.3); bevel(o, 0.04); o.data.materials.append(desk)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.25, DESK - 1.5)); o = bpy.context.object; o.scale = (14, 0.1, 2.4); o.data.materials.append(desk)
    # books and a mug at the back of the desk
    for (x, w, h, c) in ((-2.6, 0.35, 1.5, '#4a7ab8'), (-2.22, 0.3, 1.3, '#d8603a'), (-1.88, 0.38, 1.6, '#4aa860')):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 2.6, DESK + h / 2)); o = bpy.context.object; o.scale = (w, 1.1, h); bevel(o, 0.03); o.data.materials.append(mat('bk' + c, c, 0.7))
    cyl((2.5, 2.4, DESK + 0.35), 0.32, 0.7, mat('mug', '#f2c14e', 0.4, 0.3), 48)
    # the pencil standing upright in a little clay stand at the centre
    stand = mat('stand', '#d88a6a', 0.8); pen = mat('pencil', '#f2c14e', 0.6); woodtip = mat('ptip', '#f4dcb0', 0.8); lead = mat('lead', '#3a3a40', 0.5)
    cyl((0, 0.2, DESK + 0.15), 0.42, 0.3, stand, 48)
    cyl((0, 0.2, DESK + 1.55), 0.08, 2.5, pen, 6)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.08, depth=0.22, location=(0, 0.2, DESK + 2.91)); o = bpy.context.object; o.data.materials.append(woodtip)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.025, depth=0.06, location=(0, 0.2, DESK + 3.03)); o = bpy.context.object; o.data.materials.append(lead)
    render(sc, 'bg')
    META['tip'] = proj(0, 0.2, DESK + 3.06); META['desk'] = proj(0, -1.2, DESK)[1]

def build_toy():
    sc = reset(True)
    body = wood('toyw', '#e8c898', '#f2d6a8'); red = mat('toyr', '#d8483a', 0.5, 0.3); blk = mat('eye', '#1a1210', 0.9); beak = mat('beak', '#f2c14e', 0.6)
    # a round little bird sitting on the pivot, two long arms curving down to heavy acorn weights
    sphere((0, 0, 0.32), (0.3, 0.26, 0.28), red, 48)
    sphere((0, -0.02, 0.62), (0.2, 0.19, 0.19), red, 48)
    for s_ in (-1, 1): sphere((s_ * 0.08, -0.17, 0.66), (0.03, 0.015, 0.035), blk, 16)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05, depth=0.12, location=(0, -0.22, 0.6), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(beak)
    for s_ in (-1, 1):
        bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); a = bpy.context.object; a.data.bevel_depth = 0.035; a.data.dimensions = '3D'
        sp = a.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
        bp[0].co = (0, 0, 0.3); bp[1].co = (s_ * 0.9, 0, 0.18); bp[2].co = (s_ * 1.62, 0, -0.55)
        for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
        a.data.materials.append(body)
        sphere((s_ * 1.64, 0, -0.68), (0.16, 0.16, 0.19), wood('acorn', '#8a5a32', '#9a6a3e'), 32)
        sphere((s_ * 1.64, 0, -0.55), (0.17, 0.17, 0.08), noise_mat('cap', '#6a4a2a', '#7a5a3a', 30, 0.9, 0.6), 32)
    side_cam(sc, 4.0, 512, -0.1, 0.0); render(sc, 'toy')

ITEMS = {'feather': 0, 'acorn': 1, 'cherry': 2, 'pebble': 3, 'button': 4, 'konpeito': 5}
def build_items():
    for name in ITEMS:
        sc = reset(True)
        if name == 'feather':
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16); o = bpy.context.object; o.scale = (0.32, 0.03, 0.09); o.rotation_euler = (0, 0.25, 0); smooth(o); o.data.materials.append(mat('fe', '#f8f4ee', 0.9))
            cyl((0, 0, 0), 0.012, 0.75, mat('fq', '#c8b8a0', 0.6), 8, rot=(0, math.radians(76), 0))
        elif name == 'acorn':
            sphere((0, 0, -0.05), (0.13, 0.13, 0.17), wood('ac', '#9a6a3e', '#aa7a48'), 32); sphere((0, 0, 0.08), (0.15, 0.15, 0.08), noise_mat('acc', '#6a4a2a', '#7a5a3a', 30, 0.9, 0.6), 32)
            cyl((0, 0, 0.17), 0.015, 0.08, mat('st', '#6a4a2a', 0.8), 8)
        elif name == 'cherry':
            for s_ in (-1, 1): sphere((s_ * 0.12, 0, -0.1), (0.12, 0.12, 0.12), mat('ch', '#d8283a', 0.25, 0.5), 32)
            bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); a = bpy.context.object; a.data.bevel_depth = 0.012; a.data.dimensions = '3D'
            sp = a.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points; bp[0].co = (-0.12, 0, 0.0); bp[1].co = (0, 0, 0.22); bp[2].co = (0.12, 0, 0.0)
            for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
            a.data.materials.append(mat('chs', '#5a8a3a', 0.7))
        elif name == 'pebble':
            sphere((0, 0, 0), (0.2, 0.16, 0.13), noise_mat('pb', '#9a9690', '#b0aca4', 12, 0.8, 0.4), 32)
        elif name == 'button':
            o = cyl((0, 0, 0), 0.15, 0.05, mat('bt', '#4a8ad8', 0.4, 0.3), 48, rot=(math.radians(90), 0, 0)); bevel(o, 0.015)
            for (x, z) in ((-0.04, 0.04), (0.04, 0.04), (-0.04, -0.04), (0.04, -0.04)): cyl((x, -0.03, z), 0.018, 0.02, mat('bh', '#2a4a78', 0.5), 12, rot=(math.radians(90), 0, 0))
        else:
            o = sphere((0, 0, 0), (0.11, 0.11, 0.11), mat('kp', '#f4a8b8', 0.4, 0.3), 32)
            for k in range(10):
                a = k * 0.628; bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, depth=0.07, location=(math.cos(a) * 0.12, -0.02, math.sin(a) * 0.12)); c = bpy.context.object; c.rotation_euler = (0, -a + math.pi / 2, 0); c.data.materials.append(mat('kp', '#f4a8b8', 0.4, 0.3))
        side_cam(sc, 0.9, 128, 0.0, 0.0); render(sc, name)

JOBS = {'bg': build_bg, 'toy': build_toy, 'items': build_items}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
