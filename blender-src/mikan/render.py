# Renders the top-down art for mikan.html: kotatsu table background, mikan + yuzu (skin and peeled), sleeping cat.
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

def cyl_flat(loc, r, d, m, verts=64, bevel=.03):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc)
    o = bpy.context.object; b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    try: bpy.ops.object.shade_smooth_by_angle()
    except Exception: pass
    o.data.materials.append(m); return o

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


def peel_mat(name, c1, c2, dimple=40, bump=.35):
    """Citrus skin: warm colour variation + small oil-gland dimples (voronoi bump)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 3
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = .35; r.color_ramp.elements[1].position = .7
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = dimple; vo.feature = 'F1'
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = .02
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .5; b.inputs['Specular IOR Level'].default_value = .25
    return m

def segment_mat(name, c1, line, n=10):
    """Peeled fruit seen from the top: n segments separated by pale grooves."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    nt.links.new(sp.outputs['Y'], at.inputs[0]); nt.links.new(sp.outputs['X'], at.inputs[1])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = n / (2 * math.pi)
    nt.links.new(at.outputs[0], mu.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'PINGPONG'; fr.inputs[1].default_value = 0.5
    nt.links.new(mu.outputs[0], fr.inputs[0])            # 0 at the grooves, .5 in the middle of a segment
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = .015; r.color_ramp.elements[1].position = .06
    r.color_ramp.elements[0].color = (*srgb(line), 1); r.color_ramp.elements[1].color = (*srgb(c1), 1)
    nt.links.new(fr.outputs[0], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 1.0
    nt.links.new(fr.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .45; b.inputs['Specular IOR Level'].default_value = .3
    b.inputs['Subsurface Weight'].default_value = .3; b.inputs['Subsurface Scale'].default_value = .1
    return m

FRUIT = {
    'mikan': dict(c1='#f08a12', c2='#f7a52a', dim=38, bump=.35, flat=.82, fruit='#f5a73c', line='#f7cf8e', cal='#4f7a2c'),
    'yuzu':  dict(c1='#e9b812', c2='#f4d23a', dim=22, bump=.8, flat=.9, fruit='#f1cf5e', line='#f8e6a6', cal='#5d7f2e'),
}

def skin(kind):
    sc = reset(); top_light(sc); k = FRUIT[kind]
    o = sphere((0, 0, 0), (1, 1, k['flat']), peel_mat('skin', k['c1'], k['c2'], k['dim'], k['bump']), 96)
    if kind == 'yuzu': displace(o, .03, .35, 2)
    # calyx: a little green star with a stem dot
    gm = mat('cal', k['cal'], .7, .1); bm = mat('stem', '#6b5a2c', .8, .05)
    for i in range(5):
        a = i / 5 * 2 * math.pi
        sphere((math.cos(a) * .07, math.sin(a) * .07, k['flat'] - .005), (.09, .045, .02), gm, 20, rot=(0, 0, a))
    cyl((0, 0, k['flat'] + .02), .04, .05, bm, 16)
    fit_render(sc, kind + '_skin', margin=.02, px=210)

def fruit(kind):
    sc = reset(); top_light(sc); k = FRUIT[kind]
    sphere((0, 0, 0), (.95, .95, k['flat'] * .93), segment_mat('seg', k['fruit'], k['line']), 96)
    # white pith strings over the top
    wm = mat('pith', '#fdf6e6', .8, .05, .2)
    random.seed(3 if kind == 'mikan' else 8)
    for i in range(13):
        a = random.uniform(0, 6.28); r0 = random.uniform(.05, .2); r1 = random.uniform(.55, .85)
        pts = []
        for t in range(9):
            u = t / 8; rr = r0 + (r1 - r0) * u; aa = a + math.sin(u * 3 + i) * .25
            z = math.sqrt(max(0, 1 - (rr / .95) ** 2)) * k['flat'] * .93 + .012
            pts.append((math.cos(aa) * rr, math.sin(aa) * rr, z))
        cu = bpy.data.curves.new('p%d' % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .007; cu.bevel_resolution = 2
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for j, p in enumerate(pts): sp.points[j].co = (*p, 1)
        ob = bpy.data.objects.new('p%d' % i, cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(wm)
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob; bpy.ops.object.convert(target='MESH')
    sphere((0, 0, k['flat'] * .93 - .01), (.1, .1, .03), wm, 24)
    fit_render(sc, kind + '_fruit', margin=.02, px=210)

def cat():
    """A grey-and-white cat asleep in a ball (top view), closed curved eyes."""
    sc = reset(); top_light(sc)
    wh = mat('cw', '#f4f0e8', .8, .1, .1); gr = mat('cg', '#aaa4a6', .85, .1, .05)
    sphere((0, 0, .3), (1.0, .82, .42), gr, 48)                       # curled body
    hd = sphere((.55, -.35, .5), (.42, .4, .3), gr, 40)                # head tucked on the body
    for sx in (-1, 1):
        cone((.55 + sx * .25, -.15, .62), .13, .0, .22, mat('cg2', '#8d8a90', .8, .1), 16, rot=(math.radians(-40), sx * math.radians(25), 0))
    # tail wraps round the front
    pts = [(-.9, .1), (-.95, -.4), (-.6, -.75), (-.1, -.85), (.25, -.72)]
    cu = bpy.data.curves.new('tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .11; cu.bevel_resolution = 4
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for j, p in enumerate(pts): sp.points[j].co = (p[0], p[1], .28, 1)
    ob = bpy.data.objects.new('tail', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat('cg2', '#8d8a90', .8, .1))
    # closed eyes: two little arcs, dark brown, plus a pink nose
    ink = mat('ink', '#3a2418', 1.0, 0.0)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=.06, minor_radius=.014, major_segments=24, minor_segments=8, location=(.55 + sx * .14, -.55, .74))
        t = bpy.context.object; t.data.materials.append(ink)
        bm_ = bmesh.new(); bm_.from_mesh(t.data)
        bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.y > -0.01], context='VERTS'); bm_.to_mesh(t.data); bm_.free()
    sphere((.55, -.6, .62), (.2, .14, .12), wh, 24)   # white muzzle
    sphere((.55, -.7, .72), (.035, .025, .02), mat('nose', '#e89a9a', .8, .05), 16)
    fit_render(sc, 'cat', px=110)

def bg():
    """Full frame top view of a kotatsu: wooden top, red quilt around, tea, a basket of mikan, a plate."""
    sc = reset(); top_light(sc); sc.render.film_transparent = False
    W, H = 7.2, 12.8
    quilt = patch_mat('quilt', '#a83c36', '#b54a40', scale=9, lo=.3, hi=.7, rough=.95)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=70, size=1, location=(0, 0, -0.3)); q = bpy.context.object; q.scale = (W + 3, H + 3, 1)
    bpy.ops.object.transform_apply(scale=True); q.data.materials.append(quilt); displace(q, .18, .9, 2); smooth(q)
    # quilting stitches: soft ridges in a diamond grid
    for i in range(-8, 9):
        for sgn in (-1, 1):
            o = box((i * 1.1, 0, -0.22), (.05, 18, .04), mat('stitch', '#8f302b', .9, .05), .02, 2, rot=(0, 0, sgn * math.radians(35)))
    wood = noise_mat('wood', '#c69060', '#cf9a69', scale=2.0, bump=.05, rough=.55)
    tx, ty0, ty1 = 3.05, -4.55, 5.25
    box((0, (ty0 + ty1) / 2, 0), (tx * 2, ty1 - ty0, .16), wood, .05, 4)
    for (x, y, sx, sy) in ((0, ty1 - .06, tx * 2, .12), (0, ty0 + .06, tx * 2, .12), (tx - .06, (ty0 + ty1) / 2, .12, ty1 - ty0), (-tx + .06, (ty0 + ty1) / 2, .12, ty1 - ty0)):
        box((x, y, .03), (sx, sy, .16), mat('edge', '#9c6a40', .5, .2), .04, 3)
    # tea cup
    cupm = mat('cup', '#6f8f86', .5, .2); tea = mat('tea', '#9bb04a', .25, .4)
    cyl_flat((-2.2, 4.4, .35), .48, .55, cupm); cyl_flat((-2.2, 4.4, .64), .4, .02, tea, 64, .005)
    # basket with mikan
    bk = noise_mat('bask', '#b88a4a', '#d4a866', scale=30, bump=.5)
    bpy.ops.mesh.primitive_torus_add(major_radius=.95, minor_radius=.09, major_segments=64, minor_segments=12, location=(2.05, 4.3, .3))
    t = bpy.context.object; smooth(t); t.data.materials.append(bk)
    cyl_flat((2.05, 4.3, .12), .95, .1, bk)
    mk = peel_mat('skin', '#f08a12', '#f7a52a', 38, .35)
    for (dx, dy) in ((-.35, .25), (.38, .2), (0, -.35)):
        sphere((2.05 + dx, 4.3 + dy, .45), (.45, .45, .37), mk, 48)
        cyl((2.05 + dx, 4.3 + dy, .83), .03, .04, mat('stem', '#6b5a2c', .8, .05), 12)
    # plate for the peeled fruit
    pm = mat('plate', '#f7f4ee', .35, .3)
    cyl_flat((1.95, -3.35, .12), 1.0, .06, pm)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=.07, major_segments=64, minor_segments=12, location=(1.95, -3.35, .16))
    t = bpy.context.object; smooth(t); t.data.materials.append(pm)
    # a small bin for the peels
    # a small dish for the peels
    cyl_flat((-2.1, -3.45, .12), .85, .06, mat('bin', '#e9e1d2', .5, .2))
    bpy.ops.mesh.primitive_torus_add(major_radius=.85, minor_radius=.06, major_segments=64, minor_segments=12, location=(-2.1, -3.45, .16))
    t = bpy.context.object; smooth(t); t.data.materials.append(mat('bin2', '#d9cdb8', .5, .2))
    w = sc.world.node_tree.nodes['Background']; w.inputs[1].default_value = .55; w.inputs[0].default_value = (*srgb('#ffe9cc'), 1)
    cam_top(sc, -W / 2, W / 2, -H / 2, H / 2, 100)
    sc.render.filepath = os.path.join(OUT, 'bg.png'); bpy.ops.render.render(write_still=True)
    print('wrote bg', flush=True)

def tex(kind):
    """A flat, evenly lit patch of skin, used as the texture of the peeled ribbon."""
    sc = reset(); k = FRUIT[kind]
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); s_ = bpy.context.object; s_.data.energy = 3.0; s_.rotation_euler = Euler((math.radians(-25), math.radians(15), 0))
    bpy.ops.mesh.primitive_plane_add(size=2); p = bpy.context.object; p.data.materials.append(peel_mat('skin', k['c1'], k['c2'], k['dim'], k['bump']))
    if kind == 'yuzu': displace(p, .02, .35, 4)
    sc.render.film_transparent = False; cam_top(sc, -.6, .6, -.6, .6, 213)
    sc.render.filepath = os.path.join(OUT, kind + '_tex.png'); bpy.ops.render.render(write_still=True); print('wrote tex', flush=True)

JOBS = {'bg': bg, 'cat': cat, 'mikan_tex': lambda: tex('mikan'), 'yuzu_tex': lambda: tex('yuzu')}
for kd in FRUIT:
    JOBS[kd + '_skin'] = (lambda kd=kd: skin(kd)); JOBS[kd + '_fruit'] = (lambda kd=kd: fruit(kd))
for name, fn in JOBS.items():
    if WHAT in ('all', name) or (WHAT.endswith('*') and name.startswith(WHAT[:-1])): fn()
