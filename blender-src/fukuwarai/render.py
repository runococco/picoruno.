# Renders the layers for fukuwarai.html: a gold folding screen and red cloth (full frame), four blank cat heads
# (no face) and the face-part sprites: eye, nose, mouth, cheek (front ortho).
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
    gold = noise_mat('gold', '#d8b058', '#e8c470', 3, 0.55, 0.15, lo=.3, hi=.8)
    gold.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.35
    edge = mat('edge', '#3a2418', 0.6)
    for i in range(4):   # four folding-screen panels, gently zig-zagged
        x = -2.7 + i * 1.8; yy = 3.0 + (0.18 if i % 2 else 0)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, yy, 0.6)); o = bpy.context.object; o.scale = (1.78, 0.06, 7.2)
        o.rotation_euler = (0, 0, 0.12 if i % 2 else -0.12); o.data.materials.append(gold)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x - 0.9, yy - 0.05, 0.6)); o = bpy.context.object; o.scale = (0.06, 0.1, 7.2); o.data.materials.append(edge)
    # painted clouds and pine on the screen (flat, slightly raised)
    cl = mat('cloud', '#f2e2b0', 0.7)
    for (x, z, w) in ((-1.4, 2.4, 1.2), (1.2, 2.9, 1.5), (0.6, -0.3, 1.0)):
        for k in range(3): sphere((x + (k - 1) * w * 0.32, 2.88, z + (0.08 if k == 1 else 0)), (w * 0.26, 0.03, 0.16), cl, 32)
    pine = mat('spine', '#3a6a4a', 0.8); trunk = mat('strunk', '#6a4428', 0.8)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.7, 2.86, 0.5)); o = bpy.context.object; o.scale = (0.12, 0.02, 1.6); o.rotation_euler = (0, 0.25, 0); o.data.materials.append(trunk)
    for (x, z) in ((-1.9, 1.3), (-1.3, 1.0), (-2.1, 0.7)): sphere((x, 2.85, z), (0.42, 0.03, 0.16), pine, 32)
    # red felt cloth on the floor
    red = noise_mat('felt', '#c83a3a', '#d84848', 60, 0.95, 0.2, detail=2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -20, -2.9)); o = bpy.context.object; o.scale = (10, 50, 1); o.data.materials.append(red)
    # a little kagami-mochi on the side
    mochi = mat('mochi', '#fbf6ec', 0.8, 0.1, sss=0.2); ora = mat('daidai', '#f09030', 0.7); tray = wood('sanbo', '#c8a060', '#d8b070')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.75, -5, -2.6)); o = bpy.context.object; o.scale = (0.8, 0.8, 0.5); o.data.materials.append(tray); bevel(o, 0.03)
    sphere((1.75, -5, -2.15), (0.36, 0.36, 0.17), mochi, 48); sphere((1.75, -5, -1.92), (0.27, 0.27, 0.13), mochi, 48); sphere((1.75, -5, -1.72), (0.11, 0.11, 0.1), ora, 24)
    render(sc, 'bg')

FEAT = {'eyeL': (-0.5, 0.12), 'eyeR': (0.5, 0.12), 'nose': (0, -0.2), 'mouth': (0, -0.42), 'cheekL': (-0.92, -0.32), 'cheekR': (0.92, -0.32)}

def build_heads():
    for name, fur, p1, p2, kind in (('mike', '#fbf6ec', '#e8a050', '#4a4248', 'patch'), ('tora', '#f0b060', '#d07a30', '#d07a30', 'stripe'),
                                    ('saba', '#b8bcc4', '#6a6e78', '#6a6e78', 'stripe'), ('hachi', '#fbf6ec', '#3a363c', '#3a363c', 'hachi')):
        sc = reset(True)   # a big blank cat head, facing us; the face parts are placed by the player
        fm = mat('fur' + name, fur, 0.85, 0.1, sss=0.15); m1 = mat('p1' + name, p1, 0.85, 0.1); m2 = mat('p2' + name, p2, 0.85, 0.1); inner = mat('inner', '#f0b8b0', 0.85)
        sphere((0, 0, 0), (1.6, 1.2, 1.3), fm, 96)
        for s_ in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.48, depth=0.85, location=(s_ * 0.95, 0.1, 1.2)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.5, 0)
            e.data.materials.append(fm if kind == 'stripe' else (m1 if s_ > 0 else m2) if kind == 'patch' else m2); smooth(e)
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.26, depth=0.5, location=(s_ * 0.93, -0.18, 1.18)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.5, 0); e.scale = (1, 0.3, 1); e.data.materials.append(inner); smooth(e)
        def paint(m, cutter, extra=None):
            o = sphere((0, 0, 0), (1.606, 1.206, 1.306), m, 96); cutter.hide_render = True
            bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = cutter; bo.operation = 'INTERSECT'
            if extra: extra.hide_render = True; b2 = o.modifiers.new('b2', 'BOOLEAN'); b2.object = extra; b2.operation = 'DIFFERENCE'
        def box(loc, sc_, rot=(0, 0, 0)):
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc); c = bpy.context.object; c.scale = sc_; c.rotation_euler = rot; return c
        def ball(loc, sc_):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc); c = bpy.context.object; c.scale = sc_; return c
        if kind == 'patch':
            paint(m1, ball((0.9, -0.9, 0.8), (0.62, 0.8, 0.5))); paint(m2, ball((-0.95, -0.8, 0.85), (0.5, 0.8, 0.42)))
        elif kind == 'stripe':
            for k in (-1, 0, 1): paint(m1, box((k * 0.3, -1, 1.0 - abs(k) * 0.08), (0.11, 2, 0.55), (0, k * 0.2, 0)))
            for s_ in (-1, 1):
                for k in range(2): paint(m1, box((s_ * 1.5, -0.3, 0.2 - k * 0.3), (0.5, 2, 0.09), (0, s_ * 0.15, 0)))
        else:
            paint(m2, box((0, 0, 1.0), (4, 4, 1.6)), box((0, -1.3, -0.35), (1.35, 2, 1.35), (0, math.radians(45), 0)))
        pt = side_cam(sc, 4.2, 640, 0.25)
        SPR['head'] = {'res': 640, 'pxu': 640 / 4.2, 'feat': {k: pt(*v) for k, v in FEAT.items()}}
        render(sc, 'head_' + name)

def build_parts():
    for name in ('eye', 'nose', 'mouth', 'cheek'):
        sc = reset(True)
        if name == 'eye': sphere((0, 0, 0), (0.13, 0.05, 0.15), mat('eye', '#1a1210', 0.9, 0.0), 32)
        if name == 'nose':
            o = sphere((0, 0, 0), (0.13, 0.05, 0.09), mat('nose', '#e88a8a', 0.8), 32)
            sphere((0, 0, -0.05), (0.06, 0.05, 0.06), mat('nose', '#e88a8a', 0.8), 24)
        if name == 'mouth':
            dk = mat('mouth', '#4a2c1d', 0.9)
            for s_ in (-1, 1):
                bpy.ops.mesh.primitive_torus_add(major_radius=0.11, minor_radius=0.022, location=(s_ * 0.11, 0, 0.0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(dk)
                bpy.ops.mesh.primitive_cube_add(size=1, location=(s_ * 0.11, 0, 0.08)); c = bpy.context.object; c.scale = (0.3, 0.3, 0.16); c.hide_render = True
                bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'DIFFERENCE'
        if name == 'cheek': sphere((0, 0, 0), (0.2, 0.03, 0.13), mat('cheek', '#f4a8a0', 0.9), 32)
        side_cam(sc, 0.8, 128, 0.0); SPR['part'] = {'res': 128, 'pxu': 160.0}
        render(sc, 'part_' + name)

JOBS = {'bg': build_bg, 'heads': build_heads, 'parts': build_parts}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
