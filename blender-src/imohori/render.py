# Renders the layers for imohori.html: the autumn sweet-potato field (full frame) and the vine / potato / basket sprites
# (same raised camera angle, anchors recorded in scene.json).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 34.0; TZ = 0.0     # looking down at the field; ortho height 8 units
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


def heart_mesh(name, m, s=0.2):
    """flat heart-shaped sweet-potato leaf, tip pointing +y"""
    bm = bmesh.new(); pts = []
    for k in range(48):
        t = k / 48 * math.tau
        x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(bm.verts.new((x / 17 * s, -y / 17 * s, 0)))
    f = bm.faces.new(pts); bmesh.ops.triangulate(bm, faces=[f])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); me.materials.append(m)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.012
    return o

def vine(cx, cy, leaf_cols, n=11, size=0.22, spread=0.45, seed=1, stem_col='#6a4a5a'):
    rnd = random.Random(seed); stem = mat('stem' + stem_col, stem_col, 0.7)
    lm = [mat('leaf' + c, c, 0.65, 0.12) for c in leaf_cols]
    for k in range(n):
        a = k / n * math.tau + rnd.random() * 0.5; r = spread * (0.25 + 0.75 * rnd.random()) if k else 0
        tip = Vector((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8, 0.12 + rnd.random() * 0.22))
        base = Vector((cx, cy, 0)); d = tip - base
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.012, depth=d.length, location=(base + tip) / 2)
        st = bpy.context.object; st.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); st.data.materials.append(stem)
        lf = heart_mesh(f'lf{seed}_{k}', lm[k % len(lm)], size * (0.75 + rnd.random() * 0.4))
        lf.location = tip; lf.rotation_euler = (math.radians(-25 + rnd.random() * 50), math.radians(rnd.random() * 30 - 15), a - math.pi / 2 + rnd.random() * 0.6)

def build_bg():
    sc = reset(False)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#d6eaf2'), 1); w.inputs[1].default_value = 0.9
    random.seed(5)
    soil = noise_mat('soil', '#8a5a3a', '#a06a44', 14, 0.95, 0.6)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2.6, 0)); f = bpy.context.object; f.scale = (12, 11.6, 1); f.data.materials.append(soil)
    ridge = noise_mat('ridge', '#946240', '#ac7650', 16, 0.95, 0.7)
    for y in (1.5, -0.6, -2.7):
        sphere((0, y, 0.0), (6.5, 0.66, 0.36), ridge, 64)
    # grass verge behind the field, hills and a few trees
    grass = noise_mat('grass', '#8ab050', '#a8c460', 8, 0.9, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 4.0, -0.01)); g = bpy.context.object; g.scale = (14, 2.0, 1); g.data.materials.append(grass)
    hill = noise_mat('hill', '#7aa04a', '#98b85a', 4, 0.9, 0.3)
    for (x, y, r, h) in ((-3.2, 4.9, 3.5, 0.42), (1.5, 5.2, 4.5, 0.5), (5.0, 4.8, 3.0, 0.36)):
        sphere((x, y, 0), (r, 0.5, h), hill, 48)
    bark = noise_mat('bark', '#5a3a28', '#6a4632', 12, 0.95, 0.5)
    folc = [mat(f'fol{i}', c, 0.8, 0.1) for i, c in enumerate(['#e8902a', '#d8602a', '#c8a030', '#e0b040'])]
    for (tx, ty, s) in ((-2.6, 3.9, 0.7), (3.0, 3.8, 0.8), (-0.4, 4.6, 0.5)):
        cyl((tx, ty, 0.5 * s), 0.07 * s, 1.0 * s, bark, 12)
        for k in range(14):
            p = (tx + (random.random() - 0.5) * 0.9 * s, ty + (random.random() - 0.5) * 0.5 * s, s * (1.05 + random.random() * 0.6))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=s * (0.22 + random.random() * 0.14), location=p); o = bpy.context.object; smooth(o); o.data.materials.append(folc[k % 4])
    # field edge: a low bamboo rail + grass tufts in front
    bam = mat('bamboo', '#c8b070', 0.6, 0.2)
    for x in range(-5, 6): cyl((x * 0.9, 3.3, 0.22), 0.04, 0.44, bam, 10)
    cyl((0, 3.3, 0.38), 0.03, 11, bam, 10, (0, math.radians(90), 0))
    tuft = mat('tuft', '#7aa040', 0.8)
    for k in range(40):
        x = (random.random() - 0.5) * 9; y = random.choice([3.0, -6.2]) + (random.random() - 0.5) * 0.4
        for j in range(4):
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.03, depth=0.25 + random.random() * 0.15, location=(x + j * 0.04, y, 0.12)); o = bpy.context.object; o.rotation_euler = (random.random() * 0.5 - 0.25, random.random() * 0.5 - 0.25, 0); o.data.materials.append(tuft)
    stone = noise_mat('pebble', '#8a8078', '#a49a90', 6, 0.9, 0.5)
    for k in range(26):
        sphere(((random.random() - 0.5) * 8, -4.6 + random.random() * 7.4, 0.02), (0.05 + random.random() * 0.05, 0.04 + random.random() * 0.04, 0.03), stone, 12)
    # straw mat at the bottom where the potatoes are laid out
    straw = noise_mat('straw', '#d8b868', '#e8cc80', 30, 0.9, 0.4)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -5.6, 0.02)); o = bpy.context.object; o.scale = (6.2, 1.5, 0.04); o.data.materials.append(straw); bevel(o, 0.02, 2)
    render(sc, 'bg')
    META['ridges'] = [proj(0, y, 0.22)[1] for y in (1.5, -0.6, -2.7)]
    META['mat'] = [proj(-3.1, -5.6, 0.04), proj(3.1, -5.6, 0.04)]

def imo(name, L, R, skin, seed=1, bend=0.12):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=(0, 0, 0)); o = bpy.context.object
    for v in o.data.vertices:
        t = v.co.x; f = max(0.0, 1 - t * t) ** 0.35 * (1 + 0.15 * t) * (1 + 0.06 * math.sin(v.co.y * 9 + seed))
        v.co.x = t * L; v.co.y *= R * f; v.co.z = v.co.z * R * f * 0.92 + bend * (1 - t * t) * L * 0.4
    smooth(o); o.data.materials.append(skin)
    hair = mat('hair', '#7a4a3a', 0.9)
    for k in range(6):
        t = rnd.random() * 1.6 - 0.8; a = rnd.random() * math.tau
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.006, depth=0.08, location=(t * L, math.cos(a) * R * 0.9, math.sin(a) * R * 0.9 + bend * (1 - t * t) * L * 0.4))
        h = bpy.context.object; h.rotation_euler = (a + math.pi / 2, 0, rnd.random()); h.data.materials.append(hair)
    for s_ in (-1, 1):   # stringy tips
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=R * 0.18, depth=L * 0.25, location=(s_ * L * 1.05, 0, 0)); c = bpy.context.object
        c.rotation_euler = (0, s_ * math.radians(90), 0); c.data.materials.append(skin); smooth(c)
    return o

def build_sprites():
    for name, L, R, cols, seed in (('imo_s', 0.26, 0.11, ('#b03a50', '#c85068'), 2), ('imo_m', 0.34, 0.14, ('#a8324a', '#c04a5a'), 3),
                                   ('imo_l', 0.44, 0.18, ('#9a2c48', '#b84458'), 4), ('imo_gold', 0.44, 0.19, ('#e8a828', '#f8d050'), 5)):
        sc = reset(True)
        skin = noise_mat('skin' + name, cols[0], cols[1], 18, 0.55 if name != 'imo_gold' else 0.3, 0.25)
        if name == 'imo_gold':
            m = bpy.data.materials['skin' + name]; m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.5
        imo(name, L, R, skin, seed)
        sprite_cam(sc, 1.2, 256)
        SPR[name] = {'res': 256, 'pxu': 256 / 1.2, 'L': L}
        render(sc, name)
    for name, cols, n, size, spread, stem in (('vine', ('#5a9a3a', '#6aaa42', '#4a8a34'), 11, 0.2, 0.42, '#7a5a5a'),
                                             ('vine_big', ('#3a7a32', '#4a8a36', '#2e6a2a'), 15, 0.25, 0.55, '#6a3a5a'),
                                             ('vine_gold', ('#a8c040', '#c0cc48', '#90b038'), 11, 0.21, 0.44, '#8a7a3a')):
        sc = reset(True)
        vine(0, 0, cols, n, size, spread, seed=len(name), stem_col=stem)
        to2d = sprite_cam(sc, 1.6, 320)
        SPR[name] = {'res': 320, 'pxu': 320 / 1.6, 'root': to2d(0, 0)}
        render(sc, name)
    sc = reset(True)   # basket
    wv = noise_mat('weave', '#b88a48', '#d0a460', 40, 0.85, 0.8)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.5, depth=0.42, location=(0, 0, 0.21)); b = bpy.context.object; b.data.materials.append(wv)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in b.data.polygons: p.select = p.normal.z > 0.9
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
    sd = b.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.04; smooth(b)
    for v in b.data.vertices: v.co.x *= 1 + 0.12 * v.co.z; v.co.y *= 1 + 0.12 * v.co.z
    bpy.ops.mesh.primitive_torus_add(major_radius=0.53, minor_radius=0.035, location=(0, 0, 0.43)); t = bpy.context.object; t.data.materials.append(mat('rim', '#9a6a34', 0.8))
    to2d = sprite_cam(sc, 1.4, 320, 0.2)
    SPR['kago'] = {'res': 320, 'pxu': 320 / 1.4, 'mouth': to2d(0, 0.43)}
    render(sc, 'kago')

JOBS = {'bg': build_bg, 'sprites': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
