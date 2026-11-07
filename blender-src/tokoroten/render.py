# Renders the layers for tokoroten.html: a summer tokoroten stall seen slightly from above (back wall with a bamboo blind,
# a water tub with jelly blocks, a wooden counter), plus the wooden press (tentsuki) and plunger, porcelain and lacquer bowls
# (whole and front half), a heap of noodles, a falling bundle, a jelly block and a wooden order tag.
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

E = math.radians(15); TGT = Vector((0, 0, 2.2))      # stall camera tilted 15 deg down; 160 px per unit, frame 720 x 1280
SPOUT_Z = 2.9; BOX_H = 1.4; PL_REST = SPOUT_Z + BOX_H   # bottom of the plunger block at rest = top of the press
SIZES = {'s': 0.42, 'm': 0.54, 'l': 0.68, 'g': 0.56}

def gproj(x, y, z):
    v = (y - TGT.y) * math.sin(E) + (z - TGT.z) * math.cos(E)
    return [round(360 + (x - TGT.x) * 160, 1), round(640 - v * 160, 1)]

def tilt_cam(sc, w, h, c=(0, 0, 2.2)):
    """same tilt and pixel density as the stall frame, centred on world point c; sprite centre lands on gproj(c)"""
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    d = Vector((0, math.cos(E), -math.sin(E))); loc = Vector(c) - d * 30
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(w, h) / 160; cam.data.clip_end = 100; sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = w, h
    META.setdefault('spr', {})[sc.render.filepath or str(len(META['spr']))] = None

def light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, -10, 10)); s = bpy.context.object; s.data.energy = 2.4; s.data.angle = math.radians(25); s.data.color = srgb('#fff4e4')
    s.rotation_euler = (math.radians(40), 0, math.radians(-30))
    bpy.ops.object.light_add(type='AREA', location=(3, -8, 4)); a = bpy.context.object; a.data.energy = 700; a.data.size = 9; a.data.color = srgb('#e6f0ff')
    a.rotation_euler = (Vector((0, 0, 1)) - a.location).to_track_quat('-Z', 'Y').to_euler()

def planks(name, c1, c2, sx=6, sy=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (sx, sy, sy)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 5; wv.inputs['Detail'].default_value = 4; wv.inputs['Detail Scale'].default_value = 1.5
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7; b.inputs['Specular IOR Level'].default_value = .15
    return m

def jelly():
    m = bpy.data.materials.get('jelly')
    if m: return m
    m = mat('jelly', '#eef4e2', 0.18, 0.5, sss=0.35)
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.1
    return m

def strand(pts, r, m, square=True):
    cu = bpy.data.curves.new('st', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 0 if square else 2; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for p, q in zip(sp.bezier_points, pts): p.co = q; p.handle_left_type = p.handle_right_type = 'AUTO'
    o = bpy.data.objects.new('st', cu); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o

def grain(name, c1, c2):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.25, 9, 9)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 8; nz.inputs['Distortion'].default_value = 0.6
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    r.color_ramp.elements[0].position = .35; r.color_ramp.elements[1].position = .65
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55; b.inputs['Specular IOR Level'].default_value = .2
    return m

def build_bg():
    sc = reset(False); light(sc); tilt_cam(sc, 720, 1280)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#f4ead8'), 1)
    # back wall: wooden wainscot below, plaster above with a bamboo blind over a bright window
    box((0, 2.6, 4.5), (8, 0.2, 9), noise_mat('plaster', '#f3ead8', '#e8dcc6', 5, 0.95, 0.1), 0)
    box((0, 2.45, 0.8), (8, 0.12, 2.2), planks('wains', '#8a5c34', '#9c6a3e', 1.2, 0.2), 0.0)
    box((0, 2.38, 1.95), (8, 0.18, 0.12), wood('rail', '#6e4628', '#7e522e'), 0.01)
    box((0, 2.49, 4.5), (3.6, 0.04, 3.0), mat('sky', '#a8d6f2', 0.9, 0, emit=('#b4dcf4', 0.55)), 0)
    post = wood('post', '#6e4628', '#7e522e')
    for px in (-1.85, 1.85): box((px, 2.38, 5.0), (0.2, 0.2, 6.2), post, 0.01)
    box((0, 2.36, 3.0), (3.9, 0.16, 0.14), post, 0.01); box((0, 2.36, 6.0), (3.9, 0.16, 0.16), post, 0.01)
    bam = bamboo_mat('sudare', '#c8b070', '#d8c486')
    for i in range(30):
        cyl((0, 2.3, 4.1 + i * 0.062), 0.026, 3.5, bam, 10, rot=(0, math.radians(90), 0))
    cord = mat('cord', '#7a2e24', 0.8)
    for cx in (-1.1, 1.1): box((cx, 2.26, 5.0), (0.03, 0.02, 1.9), cord, 0)
    box((0, 2.24, 4.05), (3.5, 0.08, 0.08), bam, 0.01)
    # a red paper lantern on the left post and a wind-flag stripe on the right
    lan = mat('lantern', '#d2443a', 0.6, 0.1, sss=0.3)
    sphere((-1.45, 1.9, 4.5), (0.32, 0.32, 0.42), lan, 32)
    for lz in (4.06, 4.94): cyl((-1.45, 1.9, lz), 0.18, 0.08, mat('lcap', '#2a1c16', 0.6), 24)
    box((-1.45, 1.9, 5.3), (0.02, 0.02, 0.6), cord, 0)
    box((1.5, 2.2, 4.7), (0.36, 0.03, 1.1), noise_mat('flag', '#3c6aa8', '#4676b4', 4, 0.9, 0.05), 0.01)
    box((1.5, 2.17, 4.7), (0.24, 0.03, 0.75), mat('flagw', '#f4f2ea', 0.9), 0.01)
    # wooden arm from the wall that holds the press
    arm = wood('arm', '#7a5030', '#8c5e38')
    box((0, 1.25, PL_REST + 0.1), (0.16, 2.5, 0.16), arm, 0.02)
    box((0, 2.35, PL_REST - 0.5), (0.2, 0.12, 1.4), arm, 0.02)
    # counter: planked top, darker front face
    top = grain('ctop2', '#c08e5c', '#d4a472')
    box((0, -0.2, -0.08), (8, 2.6, 0.16), top, 0.02)
    box((0, -1.5, -1.6), (8, 0.06, 3.0), planks('cfront', '#7e5232', '#8e5e3a', 1.0, 0.25), 0)
    box((0, -1.47, -0.2), (8, 0.1, 0.1), wood('lip', '#6a4228', '#7a4e2e'), 0.01)
    # water tub with jelly blocks (back left) and a sauce jug (back right)
    oke = wood('oke', '#b88a56', '#c89a64'); hoop = mat('hoop', '#3a3432', 0.4, 0.4)
    cyl((-1.55, 1.5, 0.32), 0.5, 0.64, oke, 48); cyl((-1.55, 1.5, 0.6), 0.44, 0.01, mat('water', '#9cc8d0', 0.06, 0.4), 48)
    for hz in (0.12, 0.5): cyl((-1.55, 1.5, hz), 0.51, 0.05, hoop, 48)
    for bx, by, rz in ((-1.72, 1.45, 10), (-1.38, 1.62, -14), (-1.5, 1.3, 30)): box((bx, by, 0.62), (0.26, 0.16, 0.1), jelly(), 0.03).rotation_euler.z = math.radians(rz)
    jug = mat('jug', '#3a4a6a', 0.3, 0.4)
    cyl((1.6, 1.6, 0.35), 0.26, 0.7, jug, 32); cyl((1.6, 1.6, 0.75), 0.16, 0.12, jug, 32)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.04, location=(1.86, 1.6, 0.42), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(jug)
    cyl((1.05, 1.75, 0.06), 0.2, 0.12, mat('dish', '#f4f0e8', 0.3, 0.3), 32); cyl((1.05, 1.75, 0.13), 0.13, 0.02, mat('nori', '#4a6a3a', 0.8), 24)
    render(sc, 'bg')
    META['counter'] = gproj(0, 0, 0)[1]; META['spout'] = gproj(0, 0, SPOUT_Z); META['front'] = gproj(0, -1.47, -0.15)[1]
    META['plrest'] = gproj(0, 0, PL_REST)[1]

def bamboo_mat(name, c1, c2):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.3, 6, 6); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.45
    return m

def build_tsuki():
    """the press: an open square wooden tube with a wire grid at the bottom; sprite centred on the press middle"""
    sc = reset(True); light(sc); cz = SPOUT_Z + BOX_H / 2; tilt_cam(sc, 160, 320, (0, 0, cz))
    w = wood('tw', '#c49464', '#d2a474'); s, t = 0.24, 0.05
    for dx, dy, sx, sy in ((-s, 0, t, 2 * s + t), (s, 0, t, 2 * s + t), (0, -s, 2 * s - t, t), (0, s, 2 * s - t, t)):
        box((dx, dy, cz), (sx, sy, BOX_H), w, 0.012)
    band = wood('tb', '#8a5a34', '#9a6a3e')
    for bz in (SPOUT_Z + 0.12, SPOUT_Z + BOX_H - 0.12): box((0, 0, bz), (2 * s + t + 0.02, 2 * s + t + 0.02, 0.07), band, 0.01)
    wire = mat('wire', '#b8b8b0', 0.3, 0.6)
    for k in range(-3, 4):
        cyl((k * 0.06, 0, SPOUT_Z + 0.01), 0.006, 2 * s, wire, 6, rot=(math.radians(90), 0, 0))
        cyl((0, k * 0.06, SPOUT_Z + 0.01), 0.006, 2 * s, wire, 6, rot=(0, math.radians(90), 0))
    render(sc, 'tsuki'); META['tsuki'] = gproj(0, 0, cz)

def build_plunger():
    """plunger block + rod + crossbar, at rest; game slides it down by the push amount (sprite centred on its middle)"""
    sc = reset(True); light(sc); cz = PL_REST + 0.7; tilt_cam(sc, 220, 320, (0, 0, cz))
    w = wood('pw', '#b8865a', '#c8966a')
    box((0, 0, PL_REST + 0.08), (0.42, 0.42, 0.16), w, 0.015)
    cyl((0, 0, PL_REST + 0.7), 0.045, 1.1, w, 16)
    cyl((0, 0, PL_REST + 1.25), 0.06, 1.0, wood('ph', '#8a5a34', '#9a6a3e'), 20, rot=(0, math.radians(90), 0))
    render(sc, 'plunger'); META['plunger'] = gproj(0, 0, cz)

def bowl_mesh(r, h, mats, front=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
    if front: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=True)
    bm.to_mesh(o.data); bm.free()
    o.scale = (r, r, h); o.location = (0, 0, h); smooth(o)
    for m in mats: o.data.materials.append(m)
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.035 / r; so.offset = 1; so.material_offset = 1; so.material_offset_rim = 2
    if front: o.modifiers.new('ws', 'WEIGHTED_NORMAL')
    return o

def porcelain(name, band):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = 'CONSTANT'; el = r.color_ramp.elements
    el[0].position = 0; el[0].color = (*srgb('#f6f4ee'), 1); el[1].position = 0.58; el[1].color = (*srgb(band), 1)
    e2 = el.new(0.72); e2.color = (*srgb('#f6f4ee'), 1); e3 = el.new(0.8); e3.color = (*srgb(band), 1); e4 = el.new(0.86); e4.color = (*srgb('#f6f4ee'), 1)
    nt.links.new(sx.outputs['Z'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.25; b.inputs['Specular IOR Level'].default_value = .35
    return m

def build_bowl(k):
    r = SIZES[k]; h = r * 0.62
    for front in (False, True):
        sc = reset(True); light(sc); tilt_cam(sc, int(r * 2 * 160 + 40) // 2 * 2, int((h + 0.2) * 160 + 60) // 2 * 2, (0, 0, h / 2))
        if k == 'g': mats = [mat('lacq', '#2a1612', 0.25, 0.4), mat('lacqin', '#b02a22', 0.25, 0.4), mat('gold', '#d8a840', 0.25, 0.8)]
        else: mats = [porcelain('pc' + k, {'s': '#3a5aa0', 'm': '#2e4c8c', 'l': '#2a4a86'}[k]), mat('pin', '#f6f4ee', 0.22, 0.4), mat('prim', '#2e4c8c', 0.3, 0.4)]
        bowl_mesh(r, h, mats, front)
        cyl((0, 0, 0.03), r * 0.42, 0.06, mats[0] if k != 'g' else mats[0], 48)
        if not front:
            # shadow catcher stand-in: none (film transparent); a soft contact shadow is drawn by the game
            pass
        render(sc, 'bowl_' + k + ('f' if front else ''))
    META.setdefault('bowl', {})[k] = {'r': round(r * 160, 1), 'h': round(h * 160, 1), 'c': gproj(0, 0, h / 2), 'rim': gproj(0, 0, h)[1], 'rimRy': round(r * math.sin(E) * 160, 1)}

def build_pile():
    """a heap of square noodles sized for the large bowl (radius .62, height .42); scaled per bowl and fill in the game"""
    sc = reset(True); light(sc); tilt_cam(sc, 240, 140, (0, 0, 0.2)); m = jelly(); rnd = random.Random(7)
    R, H = 0.6, 0.42
    for i in range(170):
        a = rnd.uniform(0, math.tau); rr = R * math.sqrt(rnd.random()) * 0.9; pts = []
        L = rnd.uniform(0.35, 0.8); d = rnd.uniform(0, math.tau)
        for j in range(5):
            t = (j / 4 - 0.5) * L; x = rr * math.cos(a) + t * math.cos(d); y = rr * math.sin(a) * 0.9 + t * math.sin(d)
            q = min(1, math.hypot(x, y) / R); z = H * (1 - q * q) * rnd.uniform(0.8, 1.0) + 0.02
            pts.append((max(-R, min(R, x)), max(-R, min(R, y)), z))
        strand(pts, 0.022, m)
    render(sc, 'pile')

def build_stream():
    """a falling bundle of straight noodles, 1.6 units long"""
    sc = reset(True); light(sc); tilt_cam(sc, 80, 256, (0, 0, 0)); m = jelly(); rnd = random.Random(3)
    for i in range(14):
        x = rnd.uniform(-0.17, 0.17); y = rnd.uniform(-0.17, 0.17); wob = rnd.uniform(-0.03, 0.03)
        strand([(x, y, 0.85), (x + wob, y, 0.3), (x - wob, y, -0.3), (x, y, -0.85)], 0.02, m)
    render(sc, 'stream')

def build_block():
    sc = reset(True); light(sc); tilt_cam(sc, 100, 100, (0, 0, 0))
    o = box((0, 0, 0), (0.4, 0.4, 0.34), jelly(), 0.04)
    render(sc, 'block')

def build_fuda():
    sc = reset(True); light(sc); tilt_cam(sc, 90, 120, (0, 0, 0))
    box((0, 0, 0), (0.46, 0.06, 0.64), wood('fd', '#e2c08c', '#ecd09e'), 0.02)
    cyl((0, -0.035, 0.24), 0.03, 0.02, mat('hole2', '#5a3a22', 0.8), 16, rot=(math.radians(90), 0, 0))
    render(sc, 'fuda')

JOBS = {'bg': build_bg, 'tsuki': build_tsuki, 'plunger': build_plunger, 'pile': build_pile, 'stream': build_stream, 'block': build_block, 'fuda': build_fuda}
for k in SIZES: JOBS['bowl_' + k] = (lambda k: lambda: build_bowl(k))(k)
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
META.pop('spr', None)
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META)
json.dump(meta, open(MP, 'w'))
