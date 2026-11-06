# Renders the layers for darumaotoshi.html: the engawa + autumn garden (full frame) and the block / cat-daruma / mallet sprites
# (same slightly raised camera angle, anchors recorded in scene.json).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 14.0; TZ = 2.58    # ortho height 8 units; the floor line (y=0, z=0) lands on frame row ~1040
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
    # clear autumn afternoon: sun from the front right + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
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

def leaf_mesh(name, m, s=0.1):
    """a flat 5-lobed maple leaf"""
    bm = bmesh.new(); pts = []
    for k in range(40):
        a = k / 40 * math.tau; lobe = 0.55 + 0.45 * abs(math.cos(a * 2.5)) ** 0.6
        pts.append(bm.verts.new((math.sin(a) * s * lobe, math.cos(a) * s * lobe, 0)))
    bm.faces.new(pts); me = bpy.data.meshes.new(name); bm.to_mesh(me); me.materials.append(m); return me

def build_bg():
    sc = reset(False)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#cfe4ee'), 1); w.inputs[1].default_value = 0.9
    random.seed(4)
    # deck (engawa) boards
    for k in range(-9, 10):
        m = noise_mat(f'deck{k % 3}', ['#c89a68', '#bf9060', '#d0a474'][k % 3], '#a87848', 4, 0.75, 0.15)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(k * 0.42, -6.0, -0.06)); b = bpy.context.object; b.scale = (0.4, 15.6, 0.12); b.data.materials.append(m); bevel(b, 0.01, 2)
    edge = wood('deckedge', '#8a5e38', '#704828')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.8, -0.1)); o = bpy.context.object; o.scale = (9, 0.16, 0.2); o.data.materials.append(edge)
    # garden below the deck
    moss = noise_mat('moss', '#6a9a48', '#8ab45a', 6, 0.9, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, -0.9)); g = bpy.context.object; g.scale = (20, 13, 1); g.data.materials.append(moss)
    for (x, y, r) in ((-2.6, 4.0, 1.2), (2.4, 5.0, 1.5), (0.6, 7.5, 1.8), (-1.2, 9.0, 1.6), (3.2, 9.5, 1.2)):
        sphere((x, y, -0.9), (r, r * 0.8, r * 0.45), moss, 32)
    stone = noise_mat('stone', '#9a958a', '#b8b2a4', 5, 0.9, 0.6)
    for (x, y, s) in ((1.4, 3.2, 0.35), (2.0, 3.6, 0.25), (-0.4, 4.4, 0.3)):
        sphere((x, y, -0.7), (s * 1.3, s, s * 0.6), stone, 24)
    # maple trees: trunks + clusters of leaves
    bark = noise_mat('bark', '#5a3a28', '#6a4632', 12, 0.95, 0.5)
    lm = [mat(f'maple{i}', c, 0.75, 0.1) for i, c in enumerate(['#d8402a', '#e8602a', '#f0902a', '#c83026'])]
    for (tx, ty, th, cr) in ((-1.9, 5.5, 4.6, 1.5), (2.6, 8.0, 4.0, 1.3)):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.16, radius2=0.08, depth=th, location=(tx, ty, -0.9 + th / 2)); t = bpy.context.object; t.rotation_euler = (0, 0.06, 0); t.data.materials.append(bark)
        for k in range(70):
            a = random.random() * math.tau; rr = cr * (0.2 + random.random() * 0.8)
            p = (tx + math.cos(a) * rr * 1.2, ty + math.sin(a) * rr * 0.6, -0.9 + th + 0.4 + (random.random() - 0.5) * cr * 0.9)
            s_ = 0.16 + random.random() * 0.16
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=s_, location=p); o = bpy.context.object; smooth(o); o.data.materials.append(lm[k % 4])
            d = o.modifiers.new('d', 'DISPLACE'); tx_ = bpy.data.textures.new('n', 'CLOUDS'); tx_.noise_scale = 0.25; d.texture = tx_; d.strength = 0.07
    # bamboo fence at the back
    bam = mat('bamboo', '#c8b070', 0.6, 0.2)
    for k in range(-30, 31):
        cyl((k * 0.16, 11.5, 0.2), 0.07, 2.4, bam, 12)
    for z in (0.4, 1.2):
        cyl((0, 11.35, z), 0.04, 12, mat('rope', '#4a3a2a', 0.8), 12, (0, math.radians(90), 0))
    # posts + eave framing the view
    post = wood('post', '#6a4428', '#553418')
    for x in (-2.55, 2.55):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 1.6, 3.0)); o = bpy.context.object; o.scale = (0.32, 0.32, 6.4); o.data.materials.append(post); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.6, 6.05)); o = bpy.context.object; o.scale = (9, 0.4, 0.35); o.data.materials.append(post)
    roof = noise_mat('roof', '#5a5a62', '#6a6a72', 20, 0.8, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.0, 6.6)); o = bpy.context.object; o.scale = (9, 4, 0.3); o.rotation_euler = (math.radians(-12), 0, 0); o.data.materials.append(roof)
    # fallen leaves on the deck
    for k in range(9):
        me = leaf_mesh(f'lf{k}', lm[k % 4], 0.12)
        o = bpy.data.objects.new(f'lf{k}', me); sc.collection.objects.link(o)
        x = random.choice([-1, 1]) * (1.4 + random.random() * 1.6); o.location = (x, -0.6 - random.random() * 2.2, 0.005); o.rotation_euler = (0, 0, random.random() * 6)
    render(sc, 'bg')

BLOCKS = {'red': '#d8402e', 'yellow': '#f0b830', 'green': '#4a9a4a', 'blue': '#3a72c0', 'purple': '#8a52a8'}
BR, BH = 0.55, 0.28
def build_blocks():
    for name, col in list(BLOCKS.items()) + [('hard', None)]:
        sc = reset(True)
        if name == 'hard':
            m = wood('hardwood', '#6a4026', '#4a2a16'); band = mat('band', '#c8a040', 0.35, 0.6)
            o = cyl((0, 0, 0), BR, BH, m, 64); bevel(o, 0.03, 3)
            for z in (-0.08, 0.08): cyl((0, 0, z), BR + 0.008, 0.035, band, 64)
        else:
            m = mat('lac_' + name, col, 0.3, 0.45); o = cyl((0, 0, 0), BR, BH, m, 64); bevel(o, 0.035, 4)
        to2d = sprite_cam(sc, 1.4, 448)
        SPR['block'] = {'res': 448, 'pxu': 448 / 1.4, 'r': BR, 'h': BH, 'step': round(BH * math.cos(math.radians(ELEV)) * 448 / 1.4, 2)}
        render(sc, 'b_' + name)

def build_head():
    sc = reset(True)
    rd = mat('daruma', '#d8402e', 0.3, 0.45); wh = mat('face', '#f6e2c0', 0.6, 0.2); bk = mat('eye', '#1a1210', 0.9, 0.0); pk = mat('nose', '#f0a0a0', 0.8)
    gd = mat('gold', '#e8b840', 0.35, 0.6)
    sphere((0, 0, 0.36), (0.5, 0.46, 0.4), rd, 64)
    sphere((0, -0.2, 0.42), (0.33, 0.28, 0.23), wh, 48)                          # face
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.13, depth=0.19, location=(s_ * 0.27, 0, 0.7)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.5, 0); e.data.materials.append(rd); smooth(e)
        e.scale = (1, 1, 0.8)
        sphere((s_ * 0.12, -0.44, 0.47), (0.045, 0.02, 0.045), bk, 16)            # dot eyes
        sphere((s_ * 0.21, -0.4, 0.38), (0.05, 0.02, 0.03), pk, 12)               # blush
        bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.007, location=(s_ * 0.028, -0.465, 0.385)); t = bpy.context.object
        t.rotation_euler = (math.radians(90), 0, 0); t.data.materials.append(mat('mouth', '#4a2c1d', 0.8))      # the two humps of an ω mouth
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
        for v in t.data.vertices: v.select = v.co.y > 0.004
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    # gold belly pattern
    sphere((0, -0.4, 0.14), (0.07, 0.02, 0.07), gd, 24)                          # little gold bell
    to2d = sprite_cam(sc, 1.4, 448, 0.3)
    SPR['head'] = {'res': 448, 'pxu': 448 / 1.4, 'base': to2d(0, -0.04)}
    render(sc, 'head')

def build_mallet():
    sc = reset(True)
    wd = wood('mallet', '#e0b880', '#c89a60'); dk = wood('malletend', '#b07848', '#905a30')
    o = cyl((0, 0, 0), 0.17, 0.5, wd, 48, (0, math.radians(90), 0)); bevel(o, 0.02, 3)
    for x in (-0.25, 0.25): cyl((x, 0, 0), 0.175, 0.03, dk, 48, (0, math.radians(90), 0))
    cyl((0, 0, -0.55), 0.045, 0.95, wd, 24)
    to2d = sprite_cam(sc, 1.6, 512, -0.4)
    SPR['mallet'] = {'res': 512, 'pxu': 512 / 1.6, 'face': to2d(0.26, 0), 'grip': to2d(0, -0.95)}
    render(sc, 'mallet')

JOBS = {'bg': build_bg, 'blocks': build_blocks, 'head': build_head, 'mallet': build_mallet}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
