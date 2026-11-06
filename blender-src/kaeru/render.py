# Renders the sprites for kaeru.html (pond pieces, frog, fly, koi). Every sprite uses the same camera
# (72 deg down, 160 px per unit) so sizes match; the water itself is drawn in the game.
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 72.0; TZ = 0.0     # sprites only: camera looking down at 72 deg
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#e0f0ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # bright afternoon sun from the upper left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.4; s.data.angle = math.radians(10); s.data.color = srgb('#fff0d0')
    s.rotation_euler = Euler((math.radians(45), math.radians(-25), math.radians(-140)))
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

SC_UNITS, SRES = 1.6, 256          # every sprite: 1.6 units across at 256 px  -> 160 px per unit
def sprite_cam(sc, scale=SC_UNITS, res=SRES, elev=ELEV):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(elev); d = 30; loc = Vector((0, -math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (-loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()

def pad_mesh(r, notch=0.5, wav=0.02):
    me = bpy.data.meshes.new('pad'); bm = bmesh.new(); c0 = bm.verts.new((0, 0, 0.012)); vs = []
    N = 72
    for k in range(N + 1):
        a = notch / 2 + k / N * (math.tau - notch); rr = r * (1 + wav * math.sin(a * 7))
        vs.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0)))
    for k in range(N): bm.faces.new((c0, vs[k], vs[k + 1]))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('pad', me); bpy.context.collection.objects.link(o)
    o.modifiers.new('s', 'SOLIDIFY').thickness = 0.015
    return o

def pad_mat(name, c1, c2):
    m = bpy.data.materials.get(name)
    if m: return m
    m = noise_mat(name, c1, c2, 7, 0.45, 0.2)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    # radial veins
    tc = nt.nodes['Texture Coordinate']; sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'; nt.links.new(sep.outputs[1], at.inputs[0]); nt.links.new(sep.outputs[0], at.inputs[1])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 7; nt.links.new(at.outputs[0], mu.inputs[0])
    sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(mu.outputs[0], sn.inputs[0])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(sn.outputs[0], ab.inputs[0])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.02
    nt.links.new(ab.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = 0.45
    return m

def build_pad(name, r, c1, c2, flower=False):
    sc = reset(True)
    o = pad_mesh(r, notch=0.45); o.data.materials.append(pad_mat('pad_' + name, c1, c2)); o.rotation_euler = (0, 0, random.uniform(0, 6.28) if False else math.radians(-60))
    if flower:
        pk = noise_mat('lotus', '#f4a0c0', '#fbd8e6', 4, 0.6, 0.1); yl = mat('lotusc', '#f8d84a', 0.5, 0.2)
        for ring, (n, L, tilt, rz) in enumerate(((8, 0.2, 55, 0.04), (7, 0.17, 35, 0.07), (5, 0.12, 15, 0.1))):
            for k in range(n):
                a = k / n * math.tau + ring * 0.4
                p = sphere((math.cos(a) * L * 0.55, math.sin(a) * L * 0.55, rz + 0.05), (L * 0.55, 0.06, 0.025), pk, 16)
                p.rotation_euler = (0, -math.radians(tilt), a)
        cyl((0, 0, 0.14), 0.045, 0.04, yl, 24)
    sprite_cam(sc); render(sc, name)

def frog_body(pose):
    gr = noise_mat('frog', '#5aa83a', '#6ab848', 5, 0.45, 0.15); dk = mat('frogdk', '#3a8a2a', 0.5, 0.2); ink = mat('ink', '#20140c', 0.25, 0.5); pk = mat('cheek', '#ff9a8a', 0.7)
    yl = mat('frogbelly', '#e8f0a0', 0.6)
    sphere((0, -0.02, 0.12), (0.26, 0.3, 0.13), gr, 48)                                  # body
    sphere((0, -0.16, 0.14), (0.22, 0.16, 0.11), gr, 32)                                 # head
    for s in (-1, 1):
        sphere((s * 0.12, -0.2, 0.24), (0.075, 0.075, 0.07), gr, 24)                      # eye bumps
        sphere((s * 0.125, -0.225, 0.3), (0.034, 0.034, 0.03), ink, 16)                   # solid dot eyes on top of the bumps
        sphere((s * 0.17, -0.29, 0.15), (0.045, 0.02, 0.025), pk, 12)                     # cheeks
    for (x, y) in ((0.08, 0.1), (-0.1, 0.02), (0.02, 0.18)): sphere((x, y, 0.23), (0.04, 0.035, 0.012), dk, 12)
    if pose == 'sit':
        for s in (-1, 1):
            sphere((s * 0.27, 0.12, 0.06), (0.09, 0.16, 0.06), gr, 24, (0, 0, s * 0.3))  # folded back legs
            sphere((s * 0.33, 0.24, 0.02), (0.07, 0.05, 0.02), gr, 16)                   # back feet
            sphere((s * 0.2, -0.24, 0.04), (0.045, 0.08, 0.04), gr, 16, (0, 0, -s * 0.3)) # front legs
            for f in (-1, 0, 1): sphere((s * 0.22 + f * 0.03, -0.33, 0.01), (0.022, 0.022, 0.012), gr, 10)
    else:
        for s in (-1, 1):
            sphere((s * 0.2, 0.3, 0.1), (0.06, 0.22, 0.05), gr, 24, (0, 0, -s * 0.25))   # stretched back legs
            sphere((s * 0.28, 0.52, 0.1), (0.09, 0.07, 0.02), gr, 16)
            sphere((s * 0.2, -0.32, 0.12), (0.04, 0.1, 0.035), gr, 16, (0, 0, s * 0.35))
            sphere((s * 0.26, -0.43, 0.12), (0.05, 0.04, 0.015), gr, 12)

def build_frog(pose):
    sc = reset(True); frog_body(pose)
    for o in sc.objects:   # turn the frog around so it faces up the screen (away from the camera)
        if o.type == 'MESH': o.location.x, o.location.y = -o.location.x, -o.location.y; o.rotation_euler.z += math.pi
    sprite_cam(sc); render(sc, 'frog_' + pose)

def build_fly():
    sc = reset(True)
    bd = mat('flyb', '#3a3a4a', 0.4, 0.4); ey = mat('flye', '#a83a2a', 0.3, 0.5)
    wm = mat('flyw', '#e8f4ff', 0.1, 0.6); bsdf = wm.node_tree.nodes['Principled BSDF']; bsdf.inputs['Alpha'].default_value = 0.45
    sphere((0, 0.02, 0.2), (0.06, 0.08, 0.05), bd, 24); sphere((0, -0.07, 0.21), (0.05, 0.04, 0.04), bd, 16)
    for s in (-1, 1):
        sphere((s * 0.035, -0.09, 0.22), (0.025, 0.025, 0.025), ey, 12)
        w = sphere((s * 0.08, 0.06, 0.25), (0.08, 0.04, 0.005), wm, 16, (0, 0, s * 0.5))
    sprite_cam(sc); render(sc, 'fly')

def build_koi():
    sc = reset(True)
    wh = mat('koiw', '#fbf6ee', 0.35, 0.4, sss=0.2); og = mat('koio', '#f0702a', 0.35, 0.4); bl = mat('koib', '#2a2a2a', 0.4, 0.3)
    sphere((0, 0, 0), (0.11, 0.3, 0.07), wh, 48)
    for (x, y, sx, sy) in ((0.0, -0.17, 0.08, 0.08), (0.02, 0.03, 0.09, 0.1), (-0.02, 0.18, 0.06, 0.06)):
        sphere((x, y, 0.035), (sx, sy, 0.04), og, 32)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.12, depth=0.012, location=(0, 0.36, 0)); t = bpy.context.object; t.scale = (1, 0.7, 1); t.data.materials.append(wh)
    for s in (-1, 1): sphere((s * 0.12, -0.1, 0), (0.08, 0.035, 0.008), wh, 16, (0, 0, s * 0.6))
    for s in (-1, 1): sphere((s * 0.05, -0.25, 0.05), (0.016, 0.016, 0.016), bl, 10)
    sprite_cam(sc, elev=89); render(sc, 'koi')

def build_reeds():
    sc = reset(True)
    st = noise_mat('reed', '#7aa04a', '#9ab85a', 10, 0.7, 0.3); ct = mat('cattail', '#6a4028', 0.8)
    random.seed(4)
    for k in range(12):
        a = random.uniform(0, 6.28); r = random.uniform(0, 0.15); h = random.uniform(0.5, 0.9); lean = random.uniform(-0.25, 0.25)
        x, y = math.cos(a) * r, math.sin(a) * r
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.025, radius2=0.003, depth=h, location=(x + math.sin(lean) * h / 2, y, h / 2))
        o = bpy.context.object; o.rotation_euler = (0, lean, a); o.scale = (1, 0.35, 1); o.data.materials.append(st)
        if k % 4 == 0:
            cyl((x + math.sin(lean) * h * 0.9, y, h * 0.9), 0.03, 0.16, ct, 12, (0, lean, 0))
    sprite_cam(sc); render(sc, 'reeds')

def build_rock():
    sc = reset(True)
    rk = noise_mat('rock', '#8a8a80', '#a8a69a', 6, 0.8, 0.6); mo = noise_mat('moss', '#5a8a3a', '#7aa84a', 20, 0.9, 0.5)
    o = sphere((0, 0, 0.05), (0.42, 0.34, 0.2), rk, 48, (0, 0, 0.3))
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('rk', 'CLOUDS'); tx.noise_scale = 0.3; d.texture = tx; d.strength = 0.08
    sphere((-0.08, 0.06, 0.2), (0.22, 0.16, 0.06), mo, 24)
    sprite_cam(sc); render(sc, 'rock')

JOBS = {'pad_l': lambda: build_pad('pad_l', 0.5, '#4a9a3a', '#62b048'), 'pad_m': lambda: build_pad('pad_m', 0.4, '#4a9a3a', '#62b048'),
        'pad_s': lambda: build_pad('pad_s', 0.32, '#58a842', '#70bc52'), 'lotus': lambda: build_pad('lotus', 0.44, '#4a9a3a', '#62b048', True),
        'leaf_old': lambda: build_pad('leaf_old', 0.4, '#b8a03a', '#d0b84a'), 'frog_sit': lambda: build_frog('sit'), 'frog_jump': lambda: build_frog('jump'),
        'fly': build_fly, 'koi': build_koi, 'reeds': build_reeds, 'rock': build_rock}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
json.dump({'res': SRES, 'units': SC_UNITS, 'pxu': SRES / SC_UNITS, 'pads': {'pad_l': 0.5, 'pad_m': 0.4, 'pad_s': 0.32, 'lotus': 0.44, 'leaf_old': 0.4}}, open(os.path.join(OUT, 'scene.json'), 'w'))
