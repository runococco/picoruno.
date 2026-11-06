# Renders the side-view sprites for kamihikouki.html (paper plane, hills, houses, trees, windmill, clouds, star).
# python3 render.py <what> <outdir>      what = all | <sprite name>
# Camera: orthographic, looking along +Y (pure side view). Each sprite's frame is fitted to its bounding box and
# the ground point (0,0,0) is written to meta.json as an anchor, so the game can stand sprites on the terrain.
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
PX = 120
os.makedirs(OUT, exist_ok=True)
META_PATH = os.path.join(OUT, 'meta.json')
META = json.load(open(META_PATH)) if os.path.exists(META_PATH) else {}

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe4f5'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.75
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.4; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(40), math.radians(-30), math.radians(-25)))
    return sc

def mat(name, color, rough=0.75, spec=0.15, sss=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Scale'].default_value = 0.1
    return m

def noise_mat(name, c1, c2, scale=6, rough=0.85, bump=0.3, lo=.35, hi=.7):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .12
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(loc, size, m, bevel=0.03, seg=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.rotation_euler = rot
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    smooth(o); o.data.materials.append(m); return o

def sphere(loc, scale, m, seg=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = scale; o.rotation_euler = rot; smooth(o); o.data.materials.append(m); return o

def cyl(loc, r, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; smooth(o); o.data.materials.append(m); return o

def cone(loc, r1, r2, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    if verts > 8: smooth(o)
    o.data.materials.append(m); return o

def displace(o, strength, size, lv=2):
    s = o.modifiers.new('s', 'SUBSURF'); s.levels = s.render_levels = lv
    t = bpy.data.textures.new('t' + o.name, 'CLOUDS'); t.noise_scale = size
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = strength; d.texture_coords = 'OBJECT'
    return o

def face(x, y, z, s=1.0, cheeks=True):
    """Face on a surface whose normal is -Y (towards the camera)."""
    blk = mat('eye', (0.02, 0.015, 0.012), 1.0, 0.0); pnk = mat('cheek', '#f2a0a0', 1.0, 0.0)
    for sx in (-1, 1):
        sphere((x + sx * 0.07 * s, y, z), (0.028 * s, 0.012, 0.028 * s), blk, 20)
        if cheeks: sphere((x + sx * 0.125 * s, y + 0.002, z - 0.04 * s), (0.03 * s, 0.008, 0.018 * s), pnk, 16)

def fit_render(sc, name, margin=0.04, px=PX):
    """Fit an ortho side camera to the scene's mesh bounds, render, store the ground anchor."""
    dg = bpy.context.evaluated_depsgraph_get()
    xs, zs = [], []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh()
        for v in me.vertices:
            w = e.matrix_world @ v.co; xs.append(w.x); zs.append(w.z)
        e.to_mesh_clear()
    x0, x1, z0, z1 = min(xs) - margin, max(xs) + margin, min(zs) - margin, max(zs) + margin
    w, h = x1 - x0, z1 - z0
    bpy.ops.object.camera_add(location=((x0 + x1) / 2, -30, (z0 + z1) / 2), rotation=(math.radians(90), 0, 0))
    c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = max(w, h); c.data.clip_end = 100
    sc.camera = c
    sc.render.resolution_x = max(4, int(round(w * px))); sc.render.resolution_y = max(4, int(round(h * px)))
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    META[name] = {'w': w, 'h': h, 'ax': -x0 / w, 'ay': z1 / h}   # anchor (world origin) in fractions of the image
    json.dump(META, open(META_PATH, 'w'), indent=1)
    print('wrote', name, flush=True)

# ---------------------------------------------------------------- sprites

def s_plane():
    """Paper plane flying to the right (+X); notebook paper with faint blue rules."""
    sc = reset()
    m = bpy.data.materials.new('paper'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 9
    wv.wave_profile = 'SAW'
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.94
    nt.links.new(wv.outputs['Fac'], st.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = (*srgb('#fbfaf5'), 1); mx.inputs[7].default_value = (*srgb('#a9c4e6'), 1)
    nt.links.new(st.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9; b.inputs['Specular IOR Level'].default_value = 0.1
    b.inputs['Subsurface Weight'].default_value = 0.15
    # geometry: nose at +X. two wings + two keel halves, slight dihedral
    me = bpy.data.meshes.new('plane'); o = bpy.data.objects.new('plane', me); bpy.context.collection.objects.link(o)
    bm = bmesh.new()
    L = 1.0
    nose = (L / 2, 0, 0)
    tl, tr = (-L / 2, -0.42, 0.06), (-L / 2, 0.42, 0.06)     # wing tips at the back
    kb = (-L / 2, 0, -0.16)                                   # keel bottom at the back
    k_mid = (-L / 2 + 0.02, 0, 0)
    for tri in [(nose, tl, k_mid), (nose, k_mid, tr), (nose, k_mid, kb)]:
        vs = [bm.verts.new(p) for p in tri]; bm.faces.new(vs)
    bm.to_mesh(me); bm.free()
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.006
    o.data.materials.append(m)
    # tilt towards the camera so the top of the wings shows; slight nose-up resting pose is done in game
    o.rotation_euler = (math.radians(-28), 0, 0)
    # a little face on the keel near the nose (dot eyes), facing camera
    bpy.context.view_layer.update()
    face(0.12, -0.08, -0.03, 0.55, cheeks=True)
    for ob in list(bpy.context.scene.objects):
        if ob.type == 'MESH' and ob.name.startswith('Sphere'): ob.rotation_euler = (0, 0, 0)
    fit_render(sc, 'plane', 0.03, 200)

def s_hill(i):
    sc = reset()
    random.seed(i)
    g = noise_mat('grass', '#8cbf6a', '#a6d27d', 3, 0.9, 0.4)
    W = [3.2, 4.4, 2.4][i]; H = [1.0, 1.5, 0.7][i]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (W / 2, 0.8, H); smooth(o); o.data.materials.append(g)
    bpy.ops.object.transform_apply(scale=True)
    displace(o, 0.06, 0.6)
    # cut below ground
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -2)); cut = bpy.context.object; cut.scale = (10, 10, 4); cut.hide_render = True
    bo = o.modifiers.new('bool', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    fl = [mat('fw', '#fbf6ec', 0.8), mat('fy', '#f6d36b', 0.8), mat('fp', '#f2a7b8', 0.8)]
    for k in range(int(W * 7)):
        x = random.uniform(-W / 2 * 0.85, W / 2 * 0.85)
        z = H * math.sqrt(max(0, 1 - (x / (W / 2)) ** 2)) - 0.02
        sphere((x, -0.75 * math.sqrt(max(0.05, 1 - (x / (W / 2)) ** 2)), z * random.uniform(.3, .95)), (0.035, 0.02, 0.035), fl[k % 3], 8)
    fit_render(sc, f'hill{i}', 0.02)

def house_side(i):
    sc = reset()
    walls = ['#f3e6cf', '#f1cfc6', '#cfe3d6', '#efe0a8'][i]
    roofs = ['#c9584c', '#5f7fb0', '#d08a3c', '#6aa07f'][i]
    wall = noise_mat('wall%d' % i, walls, walls, 9)
    roof = noise_mat('roof%d' % i, roofs, roofs, 12)
    W, D, H = [(0.9, 0.7, 0.62), (0.7, 0.6, 0.95), (1.1, 0.7, 0.55), (0.8, 0.7, 0.75)][i]
    root = bpy.data.objects.new('root', None); bpy.context.collection.objects.link(root)
    objs = []
    objs.append(box((0, 0, H / 2), (W, D, H), wall, 0.03))
    # gable roof (ridge along X)
    me = bpy.data.meshes.new('roof'); r = bpy.data.objects.new('roof', me); bpy.context.collection.objects.link(r)
    bm = bmesh.new(); Wx, Dy, rh = W / 2 + 0.07, D / 2 + 0.07, [0.38, 0.45, 0.32, 0.4][i]
    v = [bm.verts.new(p) for p in [(-Wx, -Dy, 0), (Wx, -Dy, 0), (Wx, Dy, 0), (-Wx, Dy, 0), (-Wx, 0, rh), (Wx, 0, rh)]]
    for f in ([0, 1, 5, 4], [3, 4, 5, 2], [0, 4, 3], [1, 2, 5], [0, 3, 2, 1]): bm.faces.new([v[k] for k in f])
    bm.to_mesh(me); bm.free(); r.location = (0, 0, H)
    s = r.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.05; r.data.materials.append(roof); objs.append(r)
    frame = mat('frame', '#5a3a2c', 0.8); glass = mat('glass', '#a9cbe8', 0.4, 0.2)
    for x in ([-0.25, 0.25] if W > 0.8 else [0]):
        for z in ([0.32] if H < 0.8 else [0.32, 0.66]):
            objs.append(box((x, -D / 2 - 0.005, z), (0.17, 0.02, 0.17), frame, 0.01))
            objs.append(box((x, -D / 2 - 0.012, z), (0.13, 0.02, 0.13), glass, 0.0))
    objs.append(box((W / 2 - 0.2 if W > 0.8 else 0.0, -D / 2 - 0.005, 0.14 if W > 0.8 else 0.14), (0.16, 0.03, 0.28), mat('door', '#7a5440', 0.7), 0.02))
    if i == 0: objs.append(box((0.25, 0.1, H + 0.32), (0.11, 0.11, 0.26), mat('brick', '#8a5a48', 0.8), 0.01))
    fz = H - 0.14 if H > 0.6 else H - 0.12
    face(0 if W <= 0.8 else -0.02, -D / 2 - 0.01, fz, 1.0)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and o.parent is None: o.parent = root
    root.rotation_euler = (0, 0, math.radians(-22))
    fit_render(sc, f'house{i}', 0.03)

def s_tree(i):
    sc = reset(); random.seed(i + 11)
    trunk = mat('trunk', '#7a5440', 0.85)
    if i == 0:
        cyl((0, 0, 0.25), 0.07, 0.5, trunk, 16)
        g = noise_mat('leaf', '#6aa65a', '#84bd6c', 6)
        for k in range(6):
            a = k / 6 * math.tau
            sphere((math.cos(a) * 0.22, math.sin(a) * 0.12, 0.72 + random.random() * 0.18), (0.27, 0.25, 0.25), g, 24)
        sphere((0, 0, 0.98), (0.3, 0.28, 0.27), g, 24)
    elif i == 1:   # poplar
        cyl((0, 0, 0.2), 0.06, 0.4, trunk, 16)
        g = noise_mat('leaf2', '#4f8f5c', '#66a771', 6)
        o = sphere((0, 0, 1.0), (0.26, 0.26, 0.75), g, 32); displace(o, 0.05, 0.25)
    else:          # pine
        cyl((0, 0, 0.12), 0.06, 0.24, trunk, 16)
        g = noise_mat('pine', '#3f7a5e', '#4f8e6e', 10)
        for z, r in ((0.35, 0.42), (0.68, 0.32), (0.98, 0.22)): cone((0, 0, z), r, 0.02, 0.48, g)
    fit_render(sc, f'tree{i}', 0.02)

def s_windmill():
    sc = reset()
    wall = noise_mat('mill', '#f3eadb', '#faf3e8', 8)
    roof = noise_mat('millroof', '#c9584c', '#d66a5e', 12)
    cone((0, 0, 0.9), 0.5, 0.32, 1.8, wall, 48)
    cone((0, 0, 2.0), 0.4, 0.0, 0.5, roof, 48)
    box((0, -0.44, 0.22), (0.22, 0.06, 0.42), mat('door', '#7a5440', 0.7), 0.03)
    box((0, -0.36, 1.1), (0.18, 0.04, 0.2), mat('glass', '#a9cbe8', 0.4), 0.02)
    face(0, -0.42, 0.75, 1.3)
    fit_render(sc, 'windmill', 0.03)

def s_blades():
    sc = reset()
    wood = mat('bladewood', '#9a6a4a', 0.8)
    sail = mat('sail', '#f4eee2', 0.95)
    for k in range(4):
        root = bpy.data.objects.new('arm%d' % k, None); bpy.context.collection.objects.link(root)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.6, 0, 0)); a1 = bpy.context.object; a1.scale = (1.1, 0.04, 0.05); a1.data.materials.append(wood); a1.parent = root
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.64, 0.02, 0.13)); a2 = bpy.context.object; a2.scale = (0.86, 0.02, 0.22); a2.data.materials.append(sail); a2.parent = root
        root.rotation_euler = (0, k * math.pi / 2, 0)
    cyl((0, -0.06, 0), 0.09, 0.14, wood, 24, (math.radians(90), 0, 0))
    bpy.context.view_layer.update()
    fit_render(sc, 'blades', 0.02)

def s_cloud(i):
    sc = reset(); random.seed(i * 5 + 3)
    m = mat('cloud', '#ffffff', 1.0, 0.0, sss=0.3)
    n = [6, 8, 5][i]
    for k in range(n):
        x = (k - (n - 1) / 2) * 0.32
        r = 0.28 + random.random() * 0.22 - abs(x) * 0.12
        sphere((x, random.uniform(-.1, .1), r * 0.6), (r * 1.1, r, r * 0.9), m, 32)
    fit_render(sc, f'cloud{i}', 0.03)

def s_star():
    sc = reset()
    m = mat('star', '#f6c445', 0.6, 0.1)
    me = bpy.data.meshes.new('star'); o = bpy.data.objects.new('star', me); bpy.context.collection.objects.link(o)
    bm = bmesh.new()
    pts = []
    for k in range(10):
        a = k * math.pi / 5 + math.pi / 2; r = 0.32 if k % 2 == 0 else 0.15
        pts.append(bm.verts.new((math.cos(a) * r, 0, math.sin(a) * r)))
    bm.faces.new(pts); bm.to_mesh(me); bm.free()
    s = o.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.1; s.offset = 0
    b = o.modifiers.new('b', 'BEVEL'); b.width = 0.03; b.segments = 4; b.limit_method = 'NONE'
    o.data.materials.append(m); smooth(o)
    face(0, -0.06, 0.0, 0.85)
    fit_render(sc, 'star', 0.03, 160)

def s_balloon():
    """A hot-air balloon obstacle drifting in the sky."""
    sc = reset()
    cols = ['#e86f5c', '#f6d36b', '#7fc3c0', '#f2a7b8']
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, 0, 1.25))
    o = bpy.context.object; o.scale = (0.62, 0.62, 0.72); smooth(o)
    for k, c in enumerate(cols): o.data.materials.append(mat('bal%d' % k, c, 0.7))
    for p in o.data.polygons:
        a = math.atan2(p.center.y, p.center.x); p.material_index = int(((a + math.pi) / (2 * math.pi)) * 12) % 4
    for v in o.data.vertices:   # teardrop: pinch the bottom
        if v.co.z < 0: f = 1 + v.co.z * 0.55; v.co.x *= f; v.co.y *= f
    basket = noise_mat('basket', '#a8794f', '#c19463', 30, 0.9, 0.6)
    box((0, 0, 0.12), (0.26, 0.26, 0.22), basket, 0.03)
    rope = mat('rope', '#6b4a3a', 0.9)
    for sx in (-1, 1):
        cyl((sx * 0.12, -0.12, 0.42), 0.008, 0.45, rope, 8, (0, math.radians(-sx * 12), 0))
        cyl((sx * 0.12, 0.12, 0.42), 0.008, 0.45, rope, 8, (0, math.radians(-sx * 12), 0))
    face(0, -0.6, 1.2, 1.6)
    fit_render(sc, 'balloon', 0.03)

JOBS = {'plane': s_plane, 'windmill': s_windmill, 'blades': s_blades, 'star': s_star, 'balloon': s_balloon}
for i in range(3): JOBS[f'hill{i}'] = (lambda i=i: s_hill(i)); JOBS[f'tree{i}'] = (lambda i=i: s_tree(i)); JOBS[f'cloud{i}'] = (lambda i=i: s_cloud(i))
for i in range(4): JOBS[f'house{i}'] = (lambda i=i: house_side(i))

if WHAT == 'all':
    for k, f in JOBS.items(): f()
else:
    for k in WHAT.split(','): JOBS[k]()
