# Renders the layers for shabon.html: a summer veranda and garden with the cat (seen from behind) blowing through a
# straw (sky left transparent; the game paints it), and the leafy hoop sprites the bubbles float through (front ortho).
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

def build_bg():
    sc = reset(True)
    # far: a low hedge and hydrangeas, a wooden fence; near: the engawa boards the cat sits on
    hedge = noise_mat('hedge', '#5a9a52', '#6aaa5a', 10, 0.9, 0.4); fence = wood('fence', '#b08a5a', '#c09a68')
    for k in range(15):
        x = -2.8 + k * 0.4; bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 8, -1.6)); o = bpy.context.object; o.scale = (0.08, 0.05, 1.6); o.data.materials.append(fence)
    for z in (-1.2, -2.0): bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7.95, z)); o = bpy.context.object; o.scale = (7, 0.05, 0.08); o.data.materials.append(fence)
    for x in (-2.2, -1.0, 0.3, 1.5, 2.6): sphere((x, 6, -2.5), (0.8, 0.5, 0.6), hedge, 32)
    ajisai = (mat('aj1', '#8aa8e8', 0.85), mat('aj2', '#b090d8', 0.85), mat('aj3', '#e0a0c8', 0.85))
    random.seed(7)
    for (cx, cz) in ((-1.9, -2.3), (1.9, -2.4)):
        for k in range(14):
            sphere((cx + random.uniform(-.45, .45), 5, cz + random.uniform(-.2, .35)), (0.16, 0.12, 0.15), ajisai[k % 3], 16)
    lawn = noise_mat('lawn', '#88b864', '#98c470', 8, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2, -3.0)); o = bpy.context.object; o.scale = (12, 14, 1); o.data.materials.append(lawn)
    board = wood('engawa', '#a87448', '#b88456')
    for k in range(6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.0 - k * 0.42, -2.75)); o = bpy.context.object; o.scale = (7, 0.4, 0.12); o.data.materials.append(board); bevel(o, 0.01, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.85, -2.95)); o = bpy.context.object; o.scale = (7, 0.2, 0.5); o.data.materials.append(wood('edge', '#8a5a32', '#9a6a3e'))
    # the cat seen from behind, sitting, holding a cup and blowing up through a straw
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); cg = mat('catg', '#5a5258', 0.85, 0.1)
    CX, CY, CZ = 0.0, -2.6, -2.2
    sphere((CX, CY, CZ), (0.5, 0.4, 0.48), cw, 48)
    sphere((CX - 0.2, CY + 0.1, CZ + 0.15), (0.24, 0.3, 0.24), co, 32)
    sphere((CX, CY + 0.05, CZ + 0.66), (0.4, 0.34, 0.34), cw, 48)
    sphere((CX + 0.15, CY + 0.12, CZ + 0.8), (0.18, 0.18, 0.14), cg, 32)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.13, depth=0.24, location=(CX + s_ * 0.22, CY + 0.05, CZ + 0.98)); e = bpy.context.object; e.rotation_euler = (math.radians(-10), s_ * 0.35, 0); e.data.materials.append(cg if s_ > 0 else co); smooth(e)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.07; tl.data.dimensions = '3D'
    sp = tl.data.splines[0]; sp.bezier_points.add(1); bp = sp.bezier_points
    bp[0].co = (CX + 0.35, CY + 0.2, CZ - 0.35); bp[1].co = (CX + 0.75, CY + 0.1, CZ - 0.3); bp[2].co = (CX + 0.85, CY - 0.05, CZ + 0.05)
    for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
    tl.data.materials.append(co)
    # a cup in the right paw and a straw rising to the upper right
    cup = mat('cup', '#7ab0d8', 0.4, 0.3)
    cyl((CX + 0.42, CY - 0.25, CZ + 0.35), 0.11, 0.2, cup, 32)
    sphere((CX + 0.42, CY - 0.33, CZ + 0.25), (0.09, 0.08, 0.08), cw, 16)
    TIP = (CX + 0.62, CY - 0.4, CZ + 1.15)
    straw = mat('straw', '#f2c84a', 0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.025, depth=1.0, location=((CX + 0.3 + TIP[0]) / 2, (CY - 0.3 + TIP[1]) / 2, (CZ + 0.62 + TIP[2]) / 2))
    o = bpy.context.object; d = Vector(TIP) - Vector((CX + 0.3, CY - 0.3, CZ + 0.62)); o.scale = (1, 1, d.length); o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(straw)
    render(sc, 'bg')
    META['tip'] = proj(*TIP); META['horizon'] = proj(0, 8, -0.2)[1]; META['cat'] = proj(CX, CY, CZ + 1.1)

def build_hoops():
    for name, ring, fl in (('green', '#5a9a52', ('#f4a0b0', '#fff0a0', '#ffffff')), ('gold', '#e8b030', ('#fff6c8', '#f2c84a', '#ffffff'))):
        sc = reset(True)   # a leafy hoop with little flowers, tilted almost flat
        rm = noise_mat('ring' + name, ring, ring, 10, 0.8, 0.4)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.8, minor_radius=0.06, location=(0, 0, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(rm); smooth(o)
        leaf = mat('leaf' + name, '#6aaa5a' if name == 'green' else '#d8a830', 0.8)
        for k in range(18):
            a = k / 18 * math.tau; l = sphere((math.cos(a) * 0.8, -0.03, math.sin(a) * 0.8), (0.1, 0.02, 0.05), leaf, 16); l.rotation_euler = (0, -a + 0.6, 0)
        for k in range(6):
            a = k / 6 * math.tau + 0.3
            for j in range(5):
                b = j / 5 * math.tau; sphere((math.cos(a) * 0.8 + math.cos(b) * 0.05, -0.08, math.sin(a) * 0.8 + math.sin(b) * 0.05), (0.04, 0.02, 0.04), mat('fl' + name + str(k % 3), fl[k % 3], 0.8), 12)
            sphere((math.cos(a) * 0.8, -0.1, math.sin(a) * 0.8), (0.025, 0.02, 0.025), mat('flc', '#f2c84a', 0.7), 8)
        objs = list(bpy.data.objects)   # lay the hoop nearly flat, far side up, so bubbles can float up through it
        bpy.ops.object.empty_add(location=(0, 0, 0)); em = bpy.context.object
        for o in objs:
            if o.type in ('MESH', 'CURVE'): o.parent = em
        em.rotation_euler = (math.radians(-70), 0, 0)
        side_cam(sc, 2.0, 256, 0.0); SPR['hoop'] = {'res': 256, 'pxu': 128.0, 'r': 0.8 * 128}
        render(sc, 'hoop_' + name)

JOBS = {'bg': build_bg, 'hoop': build_hoops}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
