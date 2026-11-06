# Renders the layers for buranko.html: a park in side view with the swing frame on the left and a long sandpit to
# the right (sky transparent; the game paints it, the chains and the seat), plus the side-view cat sprites.
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

def box(loc, sc_, m, bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sc_; o.data.materials.append(m); bevel(o, bev, 3); return o

GROUND = -1.6; PIV = (-0.7, 0.35)   # pivot of the swing (world x, z); 1 m in game = 100 px = 0.625 units
def build_bg():
    sc = reset(True)
    grass = noise_mat('grass', '#7ab85a', '#94cc6a', 6, 0.9, 0.3); sand = noise_mat('sand', '#e8d4a0', '#f0dcb0', 14, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5, GROUND)); o = bpy.context.object; o.scale = (14, 50, 1); o.data.materials.append(grass)
    box((0.85, 0.6, GROUND - 0.02), (3.1, 3.2, 0.08), sand, 0.03)
    frame_ = mat('frame', '#e05a4a', 0.5, 0.3); frame2 = mat('frame2', '#4a7ab8', 0.5, 0.3)
    px, pz = PIV
    for s_ in (-1, 1):   # A-frame legs (side view) and the top bar end
        a = math.radians(14) * s_; h = pz - GROUND + 0.1; d = h / math.cos(a)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.06, depth=d, location=(px - math.sin(a) * d / 2, 0.6, GROUND + h / 2), rotation=(0, a, 0)); o = bpy.context.object; o.data.materials.append(frame_); smooth(o)
    cyl((px, 0.3, pz), 0.09, 1.2, frame2, 32, rot=(math.radians(90), 0, 0))
    # trees and a hedge behind
    trunk = wood('trunk', '#7a5034', '#8a6040'); leaves = noise_mat('leaves', '#4a9a48', '#62b05a', 5, 0.95, 0.5); hedge = noise_mat('hedge', '#5aa050', '#6ab45a', 8, 0.95, 0.5)
    for (tx, r) in ((1.7, 1.0), (-2.2, 0.9)):
        cyl((tx, 8, GROUND + 1.4), 0.2, 2.8, trunk, 24)
        for (dx, dz, rr) in ((0, 1.6, r), (-0.6, 1.1, r * .7), (0.6, 1.2, r * .75)): sphere((tx + dx, 8.2, GROUND + 1.6 + dz), (rr, rr * 0.8, rr * 0.9), leaves, 40)
    for k in range(9): sphere((-4 + k * 1.0, 10, GROUND + 0.2), (0.7, 0.5, 0.55), hedge, 32)
    hill = noise_mat('hill', '#8ac070', '#9ccc80', 3, 0.95, 0.2)
    for k in range(4): sphere((-5 + k * 3.4, 30, GROUND - 1.0), (3.4, 2, 2.4), hill, 48)
    render(sc, 'bg')
    META['pivot'] = proj(px, 0.3, pz); META['ground'] = proj(0, -0.2, GROUND)[1]; META['sand'] = [proj(0.85 - 1.55, -0.2, GROUND)[0], proj(0.85 + 1.55, -0.2, GROUND)[0]]

def side_cat(pose):
    sc = reset(True)
    cw = mat('catw', '#fbf6ec', 0.85, 0.1); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#4a4248', 0.85, 0.1)
    blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8); inner = mat('inner', '#f0b8b0', 0.85)
    tilt = {'sit': 0, 'fly': -25, 'land': 0}[pose]
    before = set(bpy.data.objects)
    bs = (0.32, 0.27, 0.34) if pose != 'fly' else (0.36, 0.26, 0.3); B = (0, 0, 0.0)
    sphere(B, bs, cw, 64); paint_on(B, bs, co, (-0.28, -0.1, 0.15), (0.25, 0.4, 0.26))
    hl = (0.12, 0, 0.46); hs = (0.27, 0.25, 0.24); sphere(hl, hs, cw, 64)
    paint_on(hl, hs, cg, (-0.08, -0.1, 0.68), (0.24, 0.4, 0.2))
    for k, m in ((-1, cg), (1, cw)):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.09, depth=0.19, location=(hl[0] - 0.02, hl[1] + k * 0.13, hl[2] + 0.23)); e = bpy.context.object; e.rotation_euler = (k * -0.35, 0.1, 0); e.data.materials.append(m); smooth(e)
    sphere((hl[0] + 0.2, hl[1] - 0.15, hl[2] + 0.04), (0.035, 0.025, 0.05 if pose != 'fly' else 0.025), blk, 24)
    sphere((hl[0] + 0.27, hl[1] - 0.04, hl[2] - 0.04), (0.024, 0.025, 0.018), pink, 16)
    sphere((hl[0] + 0.22, hl[1] - 0.05, hl[2] - 0.1), (0.06, 0.09, 0.05), cw, 24)
    if pose == 'sit':     # paws up holding the chains, legs forward over the seat
        for k in (-1, 1): sphere((0.12, k * 0.2, 0.28), (0.07, 0.07, 0.12), cw, 24)
        sphere((0.3, -0.12, -0.24), (0.16, 0.08, 0.07), cw, 24); sphere((0.3, 0.12, -0.24), (0.16, 0.08, 0.07), cw, 24)
    elif pose == 'fly':   # stretched out, front paws reaching forward, back legs trailing
        for k in (-1, 1): sphere((0.42, k * 0.12, 0.2), (0.16, 0.07, 0.07), cw, 24)
        for k in (-1, 1): sphere((-0.38, k * 0.12, -0.16), (0.16, 0.07, 0.07), cw, 24)
    else:                 # landed: all four paws on the ground
        for dx in (-0.2, 0.2):
            for k in (-1, 1): sphere((dx, k * 0.12, -0.3), (0.09, 0.08, 0.07), cw, 24)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.05; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    bp[0].co = (-0.28, 0.05, -0.1); bp[1].co = (-0.52, 0.0, 0.0 if pose != 'fly' else -0.05); bp[2].co = (-0.6, -0.05, 0.3 if pose != 'fly' else 0.0)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    if tilt:
        bpy.ops.object.empty_add(location=(0, 0, 0)); em = bpy.context.object
        for o in set(bpy.data.objects) - before - {em}:
            if o.parent is None and not o.hide_render: o.parent = em
        em.rotation_euler = (0, math.radians(-tilt), 0)
    side_cam(sc, 1.6, 160, 0.1); render(sc, 'cat_' + pose)
    SPR['cat'] = {'res': 160, 'pxu': 100.0, 'seat': 80 + (0.1 + 0.3) * 100}

def build_cats():
    for pose in ('sit', 'fly', 'land'): side_cat(pose)

JOBS = {'bg': build_bg, 'cats': build_cats}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
