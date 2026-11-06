# Renders the layers for koma.html: a wooden-tub top arena on a plank floor seen from straight above (full frame),
# the opponent cats peeking over the rim and the spinning-top sprites (top-down ortho).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 89.9; TZ = 0.0     # straight down: frame row = 640 - y * 160
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
    # cosy room light from above-front + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
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

def top_cam(sc, scale, res):
    sprite_cam(sc, scale, res); c = sc.camera; c.location = (0, 0, 30); c.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()

AC_ = (0.0, 0.125); AR = 1.75   # arena centre (world x, y) and radius

def build_bg():
    sc = reset(False)
    plank = wood('plank', '#b48a5c', '#c09868')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.75)); o = bpy.context.object; o.scale = (10, 12, 1); o.data.materials.append(mat('under', '#6a4a30', 0.9))
    for i in range(7):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-3 + i * 1.0, 0, -0.6)); o = bpy.context.object; o.scale = (0.98, 9, 0.1); o.data.materials.append(plank); bevel(o, 0.01, 2)
    # the tub: wooden staves ring with two iron hoops, canvas dish inside
    staves = wood('staves', '#9a6a3a', '#b07c48'); iron = mat('iron', '#4a4a52', 0.5, 0.4)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=AR + 0.28, depth=0.5, location=(AC_[0], AC_[1], -0.3)); tub = bpy.context.object; tub.data.materials.append(staves)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=AR + 0.04, depth=1.0, location=(AC_[0], AC_[1], -0.3)); hole = bpy.context.object; hole.hide_render = True
    bo = tub.modifiers.new('b', 'BOOLEAN'); bo.object = hole; bo.operation = 'DIFFERENCE'
    for k in range(36):
        a = k / 36 * math.tau; bpy.ops.mesh.primitive_cube_add(size=1, location=(AC_[0] + math.cos(a) * (AR + 0.16), AC_[1] + math.sin(a) * (AR + 0.16), -0.04)); o = bpy.context.object
        o.scale = (0.02, 0.32, 0.01); o.rotation_euler = (0, 0, a); o.data.materials.append(mat('gap', '#6a4628', 0.9))
    bpy.ops.mesh.primitive_torus_add(major_radius=AR + 0.3, minor_radius=0.05, location=(AC_[0], AC_[1], -0.2)); o = bpy.context.object; o.data.materials.append(iron)
    canvas = noise_mat('canvas', '#d6c49a', '#e2d2aa', 60, 0.95, 0.25, detail=3)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, location=(AC_[0], AC_[1], -0.06)); dish = bpy.context.object; dish.scale = (AR + 0.06, AR + 0.06, 0.45); smooth(dish); dish.data.materials.append(canvas)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(AC_[0], AC_[1], 1.0)); cut = bpy.context.object; cut.scale = (6, 6, 2.1); cut.hide_render = True
    bo = dish.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    bpy.ops.mesh.primitive_torus_add(major_radius=AR + 0.03, minor_radius=0.05, location=(AC_[0], AC_[1], -0.06)); o = bpy.context.object; o.data.materials.append(mat('rope', '#c8a868', 0.9))
    # a little straw mat at the bottom for the launch spot
    goza = noise_mat('goza', '#c8b878', '#d8c888', 80, 0.9, 0.3, detail=2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -3.0, -0.48)); o = bpy.context.object; o.scale = (3.0, 1.2, 0.04); o.data.materials.append(goza); bevel(o, 0.02)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -3.0, -0.455)); o = bpy.context.object; o.scale = (3.04, 1.24, 0.01); o.data.materials.append(mat('gozaedge', '#4a6a8a', 0.9))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -3.0, -0.45)); o = bpy.context.object; o.scale = (2.9, 1.1, 0.01); o.data.materials.append(goza)
    render(sc, 'bg')
    META['arena'] = proj(AC_[0], AC_[1], 0); META['ar'] = AR * PXU; META['mat'] = proj(0, -3.0, 0)

CATS = (('shiro', '#fbf6ec', None, None, 'plain'), ('mike', '#fbf6ec', '#e8a050', '#4a4248', 'patch'), ('tora', '#f0b060', '#d07a30', None, 'stripe'),
        ('saba', '#b8bcc4', '#6a6e78', None, 'stripe'), ('hachi', '#fbf6ec', '#3a363c', None, 'hachi'))

def build_cats():
    for name, fur, p1, p2, kind in CATS:
        sc = reset(True)   # a cat peeking over the far rim, chin on its paws, face tilted toward the camera
        before = set(bpy.data.objects)
        fm = mat('fur' + name, fur, 0.85, 0.1, sss=0.15); blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8); inner = mat('inner', '#f0b8b0', 0.85)
        m1 = mat('p1' + name, p1, 0.85, 0.1) if p1 else fm; m2 = mat('p2' + name, p2, 0.85, 0.1) if p2 else m1
        head = sphere((0, 0.2, 0.5), (0.62, 0.5, 0.55), fm, 64)
        for s_ in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.2, depth=0.36, location=(s_ * 0.38, 0.55, 0.7)); e = bpy.context.object; e.rotation_euler = (math.radians(-50), s_ * 0.35, 0)
            e.data.materials.append(m1 if kind in ('patch', 'hachi') and (s_ < 0 or kind == 'hachi') else (m2 if kind == 'patch' else fm)); smooth(e)
            sphere((s_ * 0.22, -0.27, 0.62), (0.06, 0.04, 0.065), blk, 16)
            sphere((s_ * 0.36, -0.35, 0.12), (0.18, 0.22, 0.1), fm, 24)     # paws on the rim
        sphere((0, -0.31, 0.5), (0.05, 0.035, 0.035), pink, 12)
        if kind == 'patch': sphere((0.3, 0.1, 0.85), (0.32, 0.3, 0.2), m1, 32); sphere((-0.32, 0.12, 0.84), (0.28, 0.28, 0.2), m2, 32)
        if kind == 'stripe':
            for k in (-1, 0, 1): sphere((k * 0.16, 0.18, 1.0), (0.05, 0.28, 0.06), m1, 16)
        if kind == 'hachi':
            cap = sphere((0, 0.2, 0.5), (0.63, 0.51, 0.56), m1, 64)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.6, 0.5)); c1 = bpy.context.object; c1.scale = (3, 0.9, 3); c1.hide_render = True
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, 1.0)); c2 = bpy.context.object; c2.scale = (0.5, 1.5, 0.5); c2.rotation_euler = (0, math.radians(45), 0); c2.hide_render = True
            b1 = cap.modifiers.new('b', 'BOOLEAN'); b1.object = c1; b1.operation = 'INTERSECT'
            ab = cap.modifiers.new('b2', 'BOOLEAN'); ab.object = c2; ab.operation = 'DIFFERENCE'
        bpy.ops.object.empty_add(location=(0, 0, 0)); piv = bpy.context.object
        for o in set(bpy.data.objects) - before - {piv}:
            if o.hide_render or o.parent: continue
            o.parent = piv
        piv.rotation_euler = (math.radians(-62), 0, 0); piv.location = (0, -0.42, 0); bpy.context.view_layer.update()
        top_cam(sc, 1.8, 288); SPR['cat'] = {'res': 288, 'pxu': 160.0}
        render(sc, 'cat_' + name)

TOPS = (('aka', '#d84a4a', '#fbf2e0'), ('ao', '#3a6ab8', '#e8f0fa'), ('midori', '#4a9a5a', '#f0f6e0'), ('kiiro', '#e8b030', '#4a2c1d'), ('murasaki', '#8a5aa8', '#f4ecf8'), ('kuro', '#3a363c', '#e8c060'))

def build_tops():
    for name, c1, c2 in TOPS:
        sc = reset(True)   # a wooden spinning top from above: painted rings and a metal spindle
        m1 = mat('t1' + name, c1, 0.6, 0.2); m2 = mat('t2' + name, c2, 0.6, 0.2); body = wood('tw' + name, '#c89a60', '#d8aa70'); spin = mat('spindle', '#a8a8b0', 0.3, 0.6)
        bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.24, radius2=0.0, depth=0.22, location=(0, 0, -0.11), rotation=(math.radians(180), 0, 0)); o = bpy.context.object; o.data.materials.append(body); smooth(o)
        for r, m in ((0.24, m1), (0.19, m2), (0.14, m1), (0.09, m2)):
            cyl((0, 0, 0.0 + (0.24 - r) * 0.08), r, 0.03, m, 64)
        for k in range(4):
            a = k / 4 * math.tau; sphere((math.cos(a) * 0.165, math.sin(a) * 0.165, 0.035), (0.03, 0.03, 0.01), m1, 12)
        cyl((0, 0, 0.08), 0.03, 0.14, spin, 16); sphere((0, 0, 0.15), (0.035, 0.035, 0.02), spin, 16)
        top_cam(sc, 0.6, 128); SPR['top'] = {'res': 128, 'pxu': 128 / 0.6}
        render(sc, 'top_' + name)

JOBS = {'bg': build_bg, 'cats': build_cats, 'tops': build_tops}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
