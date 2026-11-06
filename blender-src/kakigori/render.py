# Renders the layers for kakigori.html: a summer shaved-ice counter with a hand-cranked ice shaver (full frame,
# camera almost level) and the crank wheel / ice mound / syrup bottle / cat-customer sprites (front ortho).
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff6e8'), 1)
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
def side_cam(sc, scale, res, tz, tx=0.0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    loc = Vector((tx, -30, tz)); bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + (x - tx) * res / scale, 1), round(res / 2 - (z - tz) * res / scale, 1)]

CUP_Z = -1.55          # cup rim height (mound base)
WHEEL = (1.45, 0.75)   # crank wheel centre (x, z)
BLADE_Z = 0.42

def tiles():
    m = bpy.data.materials.new('tiles'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*srgb('#f4f8fa'), 1); br.inputs['Color2'].default_value = (*srgb('#b8dcea'), 1); br.inputs['Mortar'].default_value = (*srgb('#b8ccd4'), 1)
    br.inputs['Scale'].default_value = 26; br.inputs['Mortar Size'].default_value = 0.012; br.offset = 0.0; br.inputs['Brick Width'].default_value = 0.5; br.inputs['Row Height'].default_value = 0.5
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.3; b.inputs['Specular IOR Level'].default_value = 0.4
    return m

def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff0e0'), 1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 3, 0), rotation=(math.radians(90), 0, 0)); w = bpy.context.object; w.scale = (12, 12, 1); w.data.materials.append(tiles())
    # wooden counter
    top = wood('ctop', '#b07a48', '#c8925a'); front = wood('cfront', '#8a5a34', '#a06c40')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.2, -2.15)); o = bpy.context.object; o.scale = (8, 3.2, 0.16); o.data.materials.append(top); bevel(o, 0.03)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.35, -3.4)); o = bpy.context.object; o.scale = (8, 0.1, 2.4); o.data.materials.append(front)
    for x in (-3, -1.5, 0, 1.5, 3): bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -1.42, -3.4)); o = bpy.context.object; o.scale = (0.05, 0.04, 2.4); o.data.materials.append(top)
    # the ice shaver: sky-blue enamel frame on a round base, ice block in a holder, screw press on top
    blue = mat('enamel', '#5ab0d8', 0.25, 0.5); cream = mat('cream', '#f8f0dc', 0.3, 0.4); steel = mat('steel', '#c8ccd0', 0.25, 0.8)
    cyl((0, 0.3, -2.0), 1.15, 0.14, blue, 64)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 1.0, 0.3, -0.5)); o = bpy.context.object; o.scale = (0.18, 0.22, 3.0); o.data.materials.append(blue); bevel(o, 0.06)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 1.1)); o = bpy.context.object; o.scale = (2.2, 0.26, 0.24); o.data.materials.append(blue); bevel(o, 0.08)
    cyl((0, 0.3, 1.38), 0.08, 0.5, steel, 24); cyl((0, 0.3, 1.66), 0.42, 0.06, cream, 32, rot=(0, 0, 0))
    for a in range(4): sphere((math.cos(a * math.pi / 2) * 0.42, 0.3 + math.sin(a * math.pi / 2) * 0.42, 1.66), (0.07, 0.07, 0.07), cream, 16)
    cyl((0, 0.3, 0.95), 0.58, 0.08, cream, 48)                      # press plate
    ice = mat('iceb', '#e4f4fc', 0.15, 0.6); ice.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.6
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.68)); o = bpy.context.object; o.scale = (1.0, 0.9, 0.42); o.data.materials.append(ice); bevel(o, 0.08)
    cyl((0, 0.3, BLADE_Z), 0.72, 0.1, steel, 64)                     # blade plate
    cyl((0, 0.3, BLADE_Z - 0.08), 0.62, 0.06, blue, 64)
    cyl((WHEEL[0] - 0.35, 0.3, WHEEL[1]), 0.06, 0.7, steel, 16, rot=(0, math.radians(90), 0))   # axle out to the wheel
    # the glass cup with a little stand
    glass = mat('glass', '#e0f2fa', 0.05, 0.6); b = glass.node_tree.nodes['Principled BSDF']; b.inputs['Transmission Weight'].default_value = 0.85
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.42, radius2=0.72, depth=0.42, location=(0, 0, CUP_Z - 0.21)); o = bpy.context.object; o.data.materials.append(glass); smooth(o)
    bpy.ops.object.modifier_add(type='SOLIDIFY'); o.modifiers[-1].thickness = 0.03
    cyl((0, 0, CUP_Z - 0.48), 0.12, 0.14, glass, 32); cyl((0, 0, CUP_Z - 0.58), 0.4, 0.05, glass, 48)
    # 氷 flag cloth at the left (the kanji is drawn by the game), a fan and a little plant
    cloth = mat('cloth', '#fbfaf4', 0.9); wave = mat('wave', '#3a7ad0', 0.8); red = mat('redb', '#d83a2a', 0.8)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.85, 1.0, 0.0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (0.9, 1.5, 1); o.data.materials.append(cloth)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.85, 0.98, -0.55), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (0.9, 0.35, 1); o.data.materials.append(wave)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.85, 0.97, 0.72), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (0.9, 0.06, 1); o.data.materials.append(red)
    cyl((-1.85, 0.99, 0.78), 0.02, 1.1, mat('pole', '#6a4a2a', 0.6), 12, rot=(0, math.radians(90), 0))
    render(sc, 'bg')
    META['cupZ'] = proj(0, 0, CUP_Z)[1]; META['cup'] = proj(0, 0, CUP_Z)
    META['blade'] = proj(0, 0.3, BLADE_Z - 0.12)[1]; META['wheel'] = proj(WHEEL[0], 0.3, WHEEL[1]); META['flag'] = proj(-1.85, 1.0, 0.1)
    META['counter'] = proj(0, -1.3, -2.07)[1]

def build_sprites():
    sc = reset(True)   # crank wheel: cream spokes, blue rim, a wooden handle knob
    blue = mat('enamel', '#5ab0d8', 0.25, 0.5); cream = mat('cream', '#f8f0dc', 0.3, 0.4); woodk = wood('knob', '#a0703a', '#c08a50')
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.06, location=(0, 0, 0), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(blue); smooth(o)
    for k in range(5):
        a = k / 5 * math.tau; cyl((math.cos(a) * 0.3, 0, math.sin(a) * 0.3), 0.035, 0.6, cream, 12, rot=(0, -a + math.pi / 2, 0))
    cyl((0, -0.03, 0), 0.12, 0.1, cream, 24, rot=(math.radians(90), 0, 0))
    cyl((0, -0.12, 0.6), 0.05, 0.2, woodk, 16, rot=(math.radians(90), 0, 0)); sphere((0, -0.24, 0.6), (0.09, 0.12, 0.09), woodk, 24)
    side_cam(sc, 1.6, 256, 0.0); SPR['wheel'] = {'res': 256, 'pxu': 160.0}
    render(sc, 'wheel')
    sc = reset(True)   # fluffy shaved-ice dome
    snow = noise_mat('snow', '#b4cad8', '#f2f6fa', 30, 0.8, 1.2, lo=.3, hi=.75, detail=8)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 0)); o = bpy.context.object; o.scale = (0.78, 0.6, 1.0)
    d = o.modifiers.new('d', 'DISPLACE'); tex = bpy.data.textures.new('cl', 'CLOUDS'); tex.noise_scale = 0.12; d.texture = tex; d.strength = 0.06
    o.data.materials.append(snow); smooth(o)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -1.0)); cut = bpy.context.object; cut.scale = (3, 3, 2)
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; cut.hide_render = True
    side_cam(sc, 2.0, 320, 0.5); SPR['mound'] = {'res': 320, 'pxu': 160.0, 'base': [160.0, 240.0], 'top': [160.0, 80.0], 'halfw': 0.78 * 160}
    render(sc, 'mound')
    for name, col in (('ichigo', '#e02838'), ('melon', '#2ab84a'), ('hawaii', '#1a88e8'), ('lemon', '#f2cc1a')):
        sc = reset(True)   # syrup bottle with a cream cap and a spout
        g = mat('bgl', '#f0f8fa', 0.05, 0.6); g.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.9
        liq = mat('liq' + name, col, 0.1, 0.6); liq.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.35
        cyl((0, 0, 0), 0.26, 0.8, g, 48); cyl((0, 0, -0.06), 0.235, 0.62, liq, 48)
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.26, radius2=0.1, depth=0.22, location=(0, 0, 0.51)); o = bpy.context.object; o.data.materials.append(g); smooth(o)
        cyl((0, 0, 0.66), 0.11, 0.1, mat('cap', '#f8f0dc', 0.4), 32); cyl((0, 0, 0.78), 0.03, 0.18, mat('spout', '#c8ccd0', 0.3, 0.7), 12)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.265, -0.02), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (0.3, 0.22, 1); o.data.materials.append(mat('label', '#fffaf0', 0.8))
        sphere((0, -0.27, -0.02), (0.07, 0.01, 0.07), mat('dot' + name, col, 0.5), 16)
        side_cam(sc, 1.4, 160, 0.25); SPR['bottle'] = {'res': 160, 'pxu': 160 / 1.4, 'spout': [80.0, round(80 - (0.87 - 0.25) * 160 / 1.4, 1)]}
        render(sc, 'b_' + name)
    for name, fur, patch, pc in (('mike', '#fbf6ec', '#e8a050', 1), ('hachi', '#fbf6ec', '#3a3a42', 2), ('tora', '#e8a858', '#c8783a', 3), ('gray', '#b8bcc4', '#9098a4', 3)):
        sc = reset(True)   # a cat customer's head peeking over the counter, facing us
        fm = mat('fur' + name, fur, 0.85, 0.1, sss=0.2); pm = mat('pat' + name, patch, 0.85, 0.1); bk = mat('eye', '#1a1210', 0.9); pk = mat('pk', '#f4a8a0', 0.8)
        sphere((0, 0, 0), (0.62, 0.5, 0.52), fm, 48)
        for s_ in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.2, depth=0.36, location=(s_ * 0.38, 0.05, 0.44)); e = bpy.context.object
            e.rotation_euler = (0, s_ * 0.45, 0); e.data.materials.append(pm if (pc == 1 and s_ < 0) or pc == 2 or pc == 3 else fm); smooth(e)
            sphere((s_ * 0.2, -0.47, 0.06), (0.06, 0.03, 0.075), bk, 16)
            sphere((s_ * 0.34, -0.42, -0.1), (0.1, 0.03, 0.06), pk, 16)
        sphere((0, -0.5, -0.06), (0.05, 0.03, 0.035), pk, 12)
        if pc == 1: sphere((-0.3, -0.25, 0.28), (0.26, 0.3, 0.2), pm, 24)
        if pc == 2:
            for s_ in (-1, 1): sphere((s_ * 0.28, -0.2, 0.25), (0.3, 0.32, 0.28), pm, 24, rot=(0, s_ * 0.5, 0))
        if pc == 3:
            for dx in (-0.12, 0, 0.12): sphere((dx, -0.28, 0.42), (0.035, 0.02, 0.1), pm, 12)
        side_cam(sc, 1.6, 200, 0.05); SPR['cat'] = {'res': 200, 'pxu': 125.0}
        render(sc, 'cat_' + name)

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
