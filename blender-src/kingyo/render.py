# Renders the top-down sprites for kingyo.html (goldfish x4 kinds x3 tail frames, poi frame, bowl, tub background).
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

def cam_top(sc, x0, x1, y0, y1, px):
    w, h = x1 - x0, y1 - y0
    bpy.ops.object.camera_add(location=((x0 + x1) / 2, (y0 + y1) / 2, 30), rotation=(0, 0, 0))
    c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = max(w, h); c.data.clip_end = 100
    sc.camera = c
    sc.render.resolution_x = max(4, int(round(w * px))); sc.render.resolution_y = max(4, int(round(h * px)))
    return w, h

def fit_render(sc, name, margin=0.04, px=PX):
    """Fit a top-down ortho camera to the mesh bounds, render, store where the world origin lands."""
    dg = bpy.context.evaluated_depsgraph_get(); xs, ys = [], []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh()
        for v in me.vertices:
            p = e.matrix_world @ v.co; xs.append(p.x); ys.append(p.y)
        e.to_mesh_clear()
    x0, x1, y0, y1 = min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin
    w, h = cam_top(sc, x0, x1, y0, y1, px)
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    META[name] = {'w': w, 'h': h, 'ax': -x0 / w, 'ay': y1 / h}
    json.dump(META, open(META_PATH, 'w'), indent=1)
    print('wrote', name, flush=True)

def top_light(sc):
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(35); s.data.color = srgb('#fff6e8')
    s.rotation_euler = Euler((math.radians(-22), math.radians(12), 0))
    bpy.ops.object.light_add(type='AREA', location=(-2, 3, 6))
    a = bpy.context.object; a.data.energy = 120; a.data.size = 6; a.rotation_euler = Euler((math.radians(-25), math.radians(-15), 0))

def patch_mat(name, c1, c2, scale=2.2, lo=.48, hi=.52, rough=.55, seed=0):
    """Two-colour patches (kohaku pattern)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed, seed * .7, 0)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 1.5
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .2
    b.inputs['Subsurface Weight'].default_value = .15; b.inputs['Subsurface Scale'].default_value = .05
    return m

def fin_mat(name, color, alpha=.72):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(color), 1); b.inputs['Roughness'].default_value = .5
    b.inputs['Alpha'].default_value = alpha; b.inputs['Specular IOR Level'].default_value = .1
    return m

# kind: body colour(s), fin colour, eye style, tail size
KINDS = {
    'aka':  dict(body='#ec4a26', belly='#f46c38', fin='#f26a3a', tail=1.0, fat=1.0),
    'kohaku': dict(body='#fbf3ea', patch='#e8432a', fin='#f6c4ae', tail=1.1, fat=1.0),
    'kuro': dict(body='#34303f', belly='#4a4558', fin='#3e3a4c', tail=1.2, fat=1.08, deme=True),
    'kin':  dict(body='#f4b52c', belly='#ffe089', fin='#f8c95a', tail=1.35, fat=1.05),
    'ranchu': dict(body='#f06a2a', belly='#ffc27a', fin='#f58a4a', tail=.8, fat=1.35),
}

def fish(kind, frame):
    sc = reset(); top_light(sc); k = KINDS[kind]
    if 'patch' in k: bm = patch_mat('body', k['body'], k['patch'], seed=3.1)
    else: bm = patch_mat('body', k['belly'], k['body'], scale=1.2, lo=.3, hi=.62)
    fm = fin_mat('fin', k['fin'], .78)
    bend = (-1, 0, 1)[frame] * math.radians(22)
    f = k['fat']
    # body: head part + rear part (rear bends with the tail)
    piv = Vector((0.02, 0, 0))
    def bent(p, s=0.45):   # rotate a point around piv (the rear half follows the tail)
        v = Vector(p) - piv; a = bend * s
        return piv + Vector((v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a), v.z))
    # body as one smooth metaball (head + middle + rear), so there is no seam
    mb = bpy.data.metaballs.new('mb'); mb.resolution = 0.02; mb.render_resolution = 0.012; mb.threshold = 0.6
    mo = bpy.data.objects.new('body', mb); bpy.context.collection.objects.link(mo); mo.data.materials.append(bm)
    K = float(os.environ.get('MBK', '1.55'))
    for (x, sx, sy, sz, s) in ((0.16, .3, .22, .19, 0), (-0.02, .3, .22, .19, 0.2), (-0.2, .26, .15, .14, 0.45), (-0.33, .14, .07, .07, 0.8)):
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = bent((x, 0, 0), s); e.radius = 1.0
        e.size_x, e.size_y, e.size_z = sx * K, sy * f * K, sz * f * K
        e.rotation = Euler((0, 0, bend * s)).to_quaternion()
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT'); mo.select_set(True); bpy.context.view_layer.objects.active = mo
    bpy.ops.object.convert(target='MESH'); smooth(bpy.context.object)
    root = bent((-0.4, 0, 0))
    # tail: two fan lobes (+ an inner pair for fancy tails)
    T = k['tail']; tb = bend * 1.0
    for sy in (-1, 1):
        for inner in ((0, 1) if T > 1.05 else (0,)):
            ln = 0.3 * T * (0.8 if inner else 1); sp = math.radians(24 if not inner else 12) * sy
            a = math.pi + tb + sp
            c = root + Vector((math.cos(a) * ln * .85, math.sin(a) * ln * .85, -0.01 - inner * .01))
            sphere(c, (ln, 0.13 * T * (0.7 if inner else 1), 0.012), fm, 32, rot=(0, 0, a))
    # dorsal fin along the back
    sphere(bent((-0.05, 0, 0.17 * f)), (0.2, 0.02, 0.06), fm, 24, rot=(0, 0, bend * .3))
    # pectoral fins
    for sy in (-1, 1):
        sphere((0.12, sy * 0.24 * f, -0.06), (0.1, 0.06, 0.01), fm, 24, rot=(0, 0, sy * math.radians(-35)))
    # eyes: solid round black dots, sitting on top of the head sides
    blk = mat('eye', (0.015, 0.012, 0.012), 1.0, 0.0)
    if k.get('deme'):
        for sy in (-1, 1):
            cyl((0.3, sy * 0.19, 0.06), 0.05, 0.08, bm, 24, rot=(math.radians(90), 0, 0)).location.y = sy * 0.2
            sphere((0.31, sy * 0.25, 0.07), (0.075, 0.06, 0.075), blk, 28)
    else:
        for sy in (-1, 1):
            sphere((0.33, sy * 0.135 * f, 0.1), (0.04, 0.035, 0.035), blk, 24)
    fit_render(sc, f'{kind}{frame}', px=170)

def poi():
    sc = reset(); top_light(sc)
    pm = mat('poi', '#f5f1ea', .45, .3); hm = mat('poih', '#e04f3c', .45, .3)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.04, major_segments=72, minor_segments=16)
    t = bpy.context.object; smooth(t); t.data.materials.append(hm)
    box((0, -0.86, 0), (0.12, 0.72, 0.05), hm, 0.025)
    fit_render(sc, 'poi', px=200)

def bowl():
    sc = reset(); top_light(sc)
    wm = mat('bowl', '#fbfaf6', .35, .3); inn = mat('bowlin', '#cfe8f1', .4, .2)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.06, major_segments=80, minor_segments=16)
    t = bpy.context.object; smooth(t); t.data.materials.append(wm)
    # inside: shallow dish, light so the fish drawn on top read well
    sphere((0, 0, -0.05), (0.61, 0.61, 0.25), inn, 64)
    fit_render(sc, 'bowl', px=200)

def bg():
    """Full-frame top view: a blue plastic tub on a wooden stall, night festival light."""
    sc = reset(); top_light(sc)
    sc.render.film_transparent = False
    W, H = 7.2, 12.8
    wood = noise_mat('wood', '#9a6a43', '#b9875a', scale=3, bump=.15)
    # wooden stall planks
    for i in range(14):
        y = -H / 2 + i * 1.0 + .5
        o = box((0, y, -0.8), (W + 1, 0.96, 0.2), wood, 0.03)
        o.location.x = (i % 3) * 0.2
    # tub: rim + walls + floor
    rim = mat('rim', '#4f9fd8', .4, .25); wall = mat('wall', '#69b6e6', .5, .2)
    floor = noise_mat('floor', '#7cc4ef', '#8fd0f4', scale=2, bump=.05, rough=.6)
    ix, iy = 3.18, 5.95
    box((0, 0, -0.62), (ix * 2, iy * 2, 0.1), floor, 0.0)
    for (x, y, sx, sy) in ((0, iy + .15, ix * 2, .3), (0, -iy - .15, ix * 2, .3), (ix + .15, 0, .3, iy * 2 + .6), (-ix - .15, 0, .3, iy * 2 + .6)):
        box((x, y, -0.3), (sx, sy, 0.7), wall, 0.02)
        box((x, y, 0.06), (sx + .04, sy + .04, 0.08), rim, 0.035)
    # a few pebbles on the floor
    random.seed(5)
    for i in range(0):
        x = random.uniform(-ix + .3, ix - .3); y = random.uniform(-iy + .3, iy - .3); r = random.uniform(.05, .11)
        sphere((x, y, -0.57), (r, r * .8, r * .4), mat('peb%d' % (i % 3), ('#c9d7dd', '#a9c0c8', '#e4ece9')[i % 3], .8, .1), 16, rot=(0, 0, random.random() * 3))
    w = sc.world.node_tree.nodes['Background']; w.inputs[1].default_value = .5
    cam_top(sc, -W / 2, W / 2, -H / 2, H / 2, 100)
    sc.render.filepath = os.path.join(OUT, 'bg.png'); bpy.ops.render.render(write_still=True)
    META['tub'] = {'ix': ix, 'iy': iy, 'pxu': 100}; json.dump(META, open(META_PATH, 'w'), indent=1)
    print('wrote bg', flush=True)

JOBS = {'bg': bg, 'poi': poi, 'bowl': bowl}
for kd in KINDS:
    for fr in range(3): JOBS[f'{kd}{fr}'] = (lambda kd=kd, fr=fr: fish(kd, fr))
for name, fn in JOBS.items():
    if WHAT in ('all', name) or (WHAT.endswith('*') and name.startswith(WHAT[:-1])): fn()
