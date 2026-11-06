# Renders the layers for furin.html: the summer-evening veranda (full frame) and the five wind-chime sprites
# (same nearly level camera angle, hanging point recorded in scene.json).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 6.0; TZ = 3.0      # ortho height 8 units, nearly level
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff0dc'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # summer evening: low warm sun from the right + soft sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(25); s.data.color = srgb('#ffd8a8')
    s.rotation_euler = Euler((math.radians(50), math.radians(30), math.radians(25)))
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

COLS = [('#3a8ad8', '#f6f0e0'), ('#e84a4a', '#f8e070'), ('#f0b030', '#f6f0e0'), ('#3aa86a', '#f8b0c0'), ('#8a5ac8', '#a8e0f0')]
STRIPS = ['#f8e070', '#a8d8f0', '#f8b0c0', '#f6f0e0', '#c8f0a0']

def build_bg():
    sc = reset(False)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#f6c89a'), 1); w.inputs[1].default_value = 0.9
    random.seed(9)
    # evening sky gradient backdrop
    sky = bpy.data.materials.new('sky'); sky.use_nodes = True; nt = sky.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#f8c890'), 1); r.color_ramp.elements[1].color = (*srgb('#7aa8d8'), 1)
    r.color_ramp.elements[0].position = 0.45; r.color_ramp.elements[1].position = 0.8
    nt.links.new(sep.outputs['Y'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.0
    b.inputs['Base Color'].default_value = (0, 0, 0, 1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 14, 4)); p = bpy.context.object; p.scale = (20, 12, 1); p.rotation_euler = (math.radians(90), 0, 0); p.data.materials.append(sky)
    # garden: hedge, sunflowers, distant hills
    hedge = noise_mat('hedge', '#4a8a3a', '#5a9a44', 6, 0.9, 0.5)
    for k in range(-6, 7): sphere((k * 0.75, 4.5, 0.6), (0.6, 0.5, 0.75), hedge, 24)
    hill = noise_mat('hill', '#6a9a6a', '#7aa878', 3, 0.9, 0.3)
    for (x, s) in ((-3, 3.5), (2.5, 4.0)): sphere((x, 10, -0.5), (s, 1.5, 2.2), hill, 32)
    stem = mat('stem', '#4a8a34', 0.8); pet = mat('petal', '#f8c020', 0.6, 0.1); ctr = mat('seed', '#6a3a1a', 0.9)
    for (x, y, h) in ((-2.3, 3.2, 1.9), (-1.6, 3.5, 2.2), (1.9, 3.3, 2.0), (2.6, 3.6, 1.7)):
        cyl((x, y, h / 2), 0.03, h, stem, 10)
        cyl((x, y - 0.02, h), 0.13, 0.04, ctr, 24, (math.radians(80), 0, 0))
        for k in range(14):
            a = k / 14 * math.tau
            sphere((x + math.cos(a) * 0.2, y, h + math.sin(a) * 0.2), (0.09, 0.02, 0.04), pet, 8, (0, -a, 0))
        sphere((x + 0.15, y, h * 0.55), (0.14, 0.02, 0.07), stem, 8, (0, -0.5, 0))
    # veranda floor + posts + eave
    deck = noise_mat('deck', '#b8865a', '#a87a50', 4, 0.75, 0.15)
    for k in range(-9, 10):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(k * 0.42, -2.5, 0.0)); o = bpy.context.object; o.scale = (0.4, 6.0, 0.12); o.data.materials.append(deck); bevel(o, 0.01, 2)
    post = wood('post', '#6a4428', '#553418')
    for x in (-2.55, 2.55):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.6, 3.2)); o = bpy.context.object; o.scale = (0.3, 0.3, 6.4); o.data.materials.append(post); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.6, 6.2)); o = bpy.context.object; o.scale = (9, 0.3, 0.34); o.data.materials.append(post)
    roof = noise_mat('roof', '#4a4a52', '#5a5a62', 20, 0.8, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.0, 6.75)); o = bpy.context.object; o.scale = (9, 4, 0.3); o.rotation_euler = (math.radians(-10), 0, 0); o.data.materials.append(roof)
    # a sleeping cat curled on a zabuton + a mosquito-coil pig
    zb = noise_mat('zab', '#3a6ab8', '#4a7ac8', 20, 0.9, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.6, -0.6, 0.14)); z = bpy.context.object; z.scale = (0.9, 0.8, 0.12); z.data.materials.append(zb); bevel(z, 0.04, 5)
    cw = mat('catw', '#f4ecdc', 0.85, 0.1, sss=0.2); co = mat('cato', '#3a3030', 0.85, 0.1)
    sphere((-1.6, -0.6, 0.38), (0.36, 0.28, 0.2), cw, 48); sphere((-1.35, -0.75, 0.4), (0.16, 0.15, 0.14), cw, 32)
    sphere((-1.7, -0.6, 0.48), (0.16, 0.14, 0.08), co, 24); sphere((-1.3, -0.74, 0.5), (0.08, 0.07, 0.05), co, 16)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.05, depth=0.09, location=(-1.35 + s_ * 0.08, -0.74, 0.55)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.4, 0); e.data.materials.append(cw); smooth(e)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.006, location=(-1.35 + s_ * 0.055, -0.88, 0.42)); t = bpy.context.object; t.rotation_euler = (math.radians(90), 0, 0); t.data.materials.append(mat('closed', '#2a1a10', 0.9))
    tail = [(-1.95, -0.6, 0.3), (-1.9, -0.85, 0.3), (-1.6, -0.92, 0.3)]
    cu = bpy.data.curves.new('tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.05; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(tail) - 1)
    for p_, q in zip(sp.bezier_points, tail): p_.co = q; p_.handle_left_type = p_.handle_right_type = 'AUTO'
    t = bpy.data.objects.new('tail', cu); sc.collection.objects.link(t); cu.materials.append(cw)
    pig = mat('pig', '#7aa860', 0.6, 0.2)
    sphere((1.7, -0.8, 0.22), (0.2, 0.24, 0.18), pig, 32); cyl((1.7, -1.05, 0.22), 0.1, 0.06, pig, 24, (math.radians(90), 0, 0))
    for s_ in (-1, 1): sphere((1.7 + s_ * 0.035, -1.09, 0.22), (0.015, 0.01, 0.02), mat('pigd', '#2a1a10', 0.9), 8)
    render(sc, 'bg')
    META['eave'] = proj(0, 0.6, 6.03)[1]

def build_furin(i):
    sc = reset(True)
    gl = bpy.data.materials.new(f'glass{i}'); gl.use_nodes = True; b = gl.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#e0f2fa'), 1); b.inputs['Transmission Weight'].default_value = 0.9; b.inputs['Roughness'].default_value = 0.08
    paint = mat(f'paint{i}', COLS[i][0], 0.4, 0.4); paint2 = mat(f'paint2{i}', COLS[i][1], 0.4, 0.4)
    # glass bell: open-bottomed dome
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.32, location=(0, 0, 0)); d = bpy.context.object; smooth(d)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in d.data.vertices: v.select = v.co.z < -0.16
    for v in d.data.vertices: v.co.z *= 1.25
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    sd = d.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.015; d.data.materials.append(gl)
    # painted band + dots inside the glass look
    bpy.ops.mesh.primitive_torus_add(major_radius=0.27, minor_radius=0.022, location=(0, 0, -0.18)); t = bpy.context.object; t.data.materials.append(paint)
    for k in range(6):
        a = k / 6 * math.tau + 0.3
        sphere((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.12), (0.045, 0.045, 0.045), paint if k % 2 else paint2, 16)
    sphere((0, 0, 0.4), (0.05, 0.05, 0.03), paint, 16)
    # string, clapper, strip
    st = mat('string', '#c84040', 0.8)
    cyl((0, 0, 0.5), 0.006, 0.36, st, 8); cyl((0, 0, -0.15), 0.005, 0.5, st, 8)
    cyl((0, 0, -0.12), 0.035, 0.08, mat('clap', '#d8d0c0', 0.3, 0.6), 16)
    pap = noise_mat(f'strip{i}', STRIPS[i], STRIPS[i], 60, 0.95, 0.15)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.75)); s = bpy.context.object; s.scale = (0.22, 0.008, 0.7); s.data.materials.append(pap)
    to2d = sprite_cam(sc, 2.1, 256, -0.32)
    SPR['furin'] = {'res': 256, 'pxu': 256 / 2.1, 'hang': to2d(0, 0.66), 'bell': to2d(0, 0.1), 'strip': to2d(0, -0.75)}
    render(sc, f'furin{i}')

JOBS = {'bg': build_bg, 'furin': lambda: [build_furin(i) for i in range(5)]}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
