# Renders the top-down art for ochiba.html: autumn garden, leaves, broom, cat, nuts, persimmon branch, yakiimo.
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
PX = 128
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
        if o.type not in ('MESH', 'CURVE') or o.hide_render: continue
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


def mottle(name, c1, c2, c3=None, scale=5, rough=0.6, sss=0.25, vein=None):
    """Leaf material: mottled colour, optional darker edge (c3), backlit SSS so leaves glow a little."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = .35; r.color_ramp.elements[1].position = .7
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac'])
    col = r.outputs['Color']
    if c3:   # darker towards the edges: spherical gradient from the leaf centre
        gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.6, 1.6, 1.6)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
        r2 = nt.nodes.new('ShaderNodeValToRGB'); r2.color_ramp.elements[0].position = .0; r2.color_ramp.elements[1].position = .5
        r2.color_ramp.elements[0].color = (*srgb(c3), 1); r2.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(gr.outputs['Fac'], r2.inputs['Fac'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        nt.links.new(col, mx.inputs[6]); nt.links.new(r2.outputs['Color'], mx.inputs[7]); col = mx.outputs[2]
    nt.links.new(col, b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = .15
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 60
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector']); nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .25
    b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Scale'].default_value = .02
    return m

def flat_shape(name, pts, m, curl=0.0, bend=0.0, thick=0.012, sub=3):
    """Leaf blade from a 2D outline (star-shaped around the origin): fan-filled, subdivided, curled, thickened."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    c = bm.verts.new((0, 0, 0)); vs = [bm.verts.new((x, y, 0)) for x, y in pts]
    for i in range(len(vs)): bm.faces.new((c, vs[i], vs[(i + 1) % len(vs)]))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.verts[0] is c or e.verts[1] is c], cuts=sub, use_grid_fill=False)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        v.co.z = curl * x * x + bend * y * y + 0.03 * math.sin(x * 9) * math.cos(y * 7)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    so = o.modifiers.new('so', 'SOLIDIFY'); so.thickness = thick
    smooth(o); return o

def vein(a, b, r, m):
    a = Vector(a); b = Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(m); smooth(o); return o

def zf(x, y, curl, bend): return curl * x * x + bend * y * y + 0.03 * math.sin(x * 9) * math.cos(y * 7) + 0.012

LEAVES = {   # name: (shape, c1, c2, edge, vein colour)
    'momiji_r': ('momiji', '#c4301f', '#d8452a', '#7a1a12', '#a8291b'),
    'momiji_o': ('momiji', '#e06a1e', '#ee8b2c', '#a33a14', '#c25418'),
    'momiji_y': ('momiji', '#e8b02a', '#f2c84a', '#c06a1a', '#d29a26'),
    'ichou':    ('ichou',  '#efc232', '#f6d65a', '#c8901a', '#ddb02e'),
    'sakura':   ('oval',   '#a8452a', '#c26a32', '#6e2a18', '#8a3a22'),
    'kaki':     ('oval2',  '#c45a26', '#d98a2e', '#6d6a22', '#a8562a'),
}

def leaf(name):
    sc = reset(); top_light(sc)
    shape, c1, c2, c3, vc = LEAVES[name]
    m = mottle(name, c1, c2, c3); vm = mat(name + 'v', vc, .7, .1)
    pts = []; veins = []
    if shape == 'momiji':
        lobes = 7; spread = math.radians(290)
        for i in range(lobes * 2 + 1):
            u = i / (lobes * 2); a = math.pi / 2 - spread / 2 + spread * u
            if i % 2 == 0:
                k = i // 2; r = 1.0 - 0.35 * abs(k - 3) / 3
                r *= 1.0 if k != 3 else 1.05
                pts.append((math.cos(a) * r, math.sin(a) * r)); veins.append((math.cos(a) * r * .92, math.sin(a) * r * .92))
            else:
                r = 0.42 - 0.08 * abs(i - lobes) / lobes
                # serrated sides of each lobe
                a0 = a - spread / (lobes * 2) * .5; a1 = a + spread / (lobes * 2) * .5
                pts.append((math.cos(a) * r, math.sin(a) * r))
        # re-sample with small teeth between tips and valleys
        P = []
        for i in range(len(pts)):
            p0, p1 = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
            P.append(tuple(p0))
            if i == len(pts) - 1: break
            for k in (1, 2, 3):
                q = p0.lerp(p1, k / 4); n = Vector((-(p1 - p0).y, (p1 - p0).x)).normalized()
                P.append(tuple(q + n * (0.03 if k % 2 else -0.0)))
        P.append((0.06, -0.18)); P.append((-0.06, -0.18))
        pts = P; curl, bend = 0.12, 0.08
        o = flat_shape(name, pts, m, curl, bend)
        for (x, y) in veins: vein((0, 0, zf(0, 0, curl, bend)), (x * .9, y * .9, zf(x, y, curl, bend)), .008, vm)
        vein((0, -0.18, 0.02), (0, -0.55, -0.02), .018, mat(name + 's', '#7a3a1e', .7, .1))   # stalk
    elif shape == 'ichou':
        n = 28
        for i in range(n + 1):
            u = i / n; a = math.radians(35 + 110 * u); r = 1.0 + 0.06 * math.sin(u * math.pi * 7)
            if abs(u - .5) < .04: r -= 0.22    # the notch in the middle
            pts.append((math.cos(a) * r, math.sin(a) * r - 0.15))
        pts.append((-0.04, -0.12)); pts.append((0.04, -0.12))
        # fan shape: origin near the stem, shift so the fan is star-shaped about (0,0.35)
        pts = [(x, y - 0.35) for x, y in pts]
        curl, bend = 0.1, 0.0
        o = flat_shape(name, pts, m, curl, bend); o.location.y = 0.35
        for i in range(9):
            a = math.radians(40 + 100 * i / 8)
            vein((0, -0.1, .02), (math.cos(a) * .78, math.sin(a) * .78 - 0.12, zf(math.cos(a) * .78, 0, curl, 0) + .005), .004, vm)
        vein((0, -0.1, .01), (0, -0.5, -0.02), .016, mat(name + 's', '#9a7a2a', .7, .1))
    else:
        L = 1.0 if shape == 'oval' else 1.05; W = 0.46 if shape == 'oval' else 0.55; n = 36
        for i in range(n):
            t = i / n * math.tau; x = math.sin(t) * W * (1 - 0.25 * math.cos(t)); y = -math.cos(t) * L
            y = y * (1 if y < 0 else 1.0); 
            tooth = 0.025 * (i % 2) if shape == 'oval' else 0
            pts.append((x * (1 + tooth), y))
        curl, bend = 0.25, 0.04
        o = flat_shape(name, pts, m, curl, bend)
        vein((0, -1.0, zf(0, -1, curl, bend)), (0, 1.0, zf(0, 1, curl, bend)), .016, vm)
        for k in range(-3, 4):
            y0 = k * .24; x1 = W * .8 * math.sqrt(max(0.05, 1 - (y0 / L) ** 2))
            for s in (-1, 1): vein((0, y0, zf(0, y0, curl, bend)), (s * x1, y0 + .28, zf(s * x1, y0 + .28, curl, bend)), .007, vm)
        vein((0, -1.0, 0.02), (0, -1.25, -0.01), .018, mat(name + 's', '#6a3a1e', .7, .1))
    fit_render(sc, name, px=PX)

def broom():
    """竹ぼうき head from above: a fan of bamboo twigs bound to a handle, tips pointing +y."""
    sc = reset(); top_light(sc)
    tw = noise_mat('twig', '#a8885a', '#c4a676', 20, .8, .2)
    dk = mat('twigdk', '#7a5e3a', .8, .1)
    random.seed(4)
    for i in range(130):
        a = math.radians(random.uniform(-38, 38)); L = random.uniform(1.6, 2.2)
        x0 = random.uniform(-.1, .1); p0 = Vector((x0, -0.2, .12))
        mid = p0 + Vector((math.sin(a) * L * .5, math.cos(a) * L * .5, .05))
        p1 = p0 + Vector((math.sin(a * 1.15) * L, math.cos(a * 1.15) * L, -0.05))
        cu = bpy.data.curves.new('tw', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = random.uniform(.012, .02); cu.bevel_resolution = 1
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        for j, (p, h) in enumerate(((p0, mid), (p1, mid))):
            bp = sp.bezier_points[j]; bp.co = p; bp.handle_left = bp.handle_right = h; bp.handle_left_type = bp.handle_right_type = 'FREE'
        sp.bezier_points[0].handle_left = p0 * 2 - mid
        sp.bezier_points[1].handle_right = p1 * 2 - mid
        ob = bpy.data.objects.new('tw', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(tw if random.random() < .8 else dk)
    # binding cords + handle stub
    cord = mat('cord', '#5a3a22', .8, .1)
    for y in (-0.15, 0.05):
        bpy.ops.mesh.primitive_torus_add(major_radius=.17, minor_radius=.03, location=(0, y, .12), rotation=(math.radians(90), 0, 0))
        bpy.context.object.data.materials.append(cord); bpy.context.object.scale = (1, 1, .6)
    cyl((0, -0.75, .14), .085, 1.2, noise_mat('bamboo', '#c9b072', '#d9c48a', 4, .4, .1), 24, (math.radians(90), 0, 0))
    for y in (-0.5, -1.0): cyl((0, y, .14), .092, .04, mat('node', '#a8904e', .5, .1), 24, (math.radians(90), 0, 0))
    fit_render(sc, 'broom', px=PX)

def cat(awake=False):
    """Calico cat curled up asleep (top view); awake = head lifted, round dot eyes open."""
    sc = reset(); top_light(sc)
    body = patch_mat('calico', '#f6f1e8', '#e39a4a', scale=3.2, lo=.6, hi=.62, rough=.85, seed=3)
    blk = patch_mat('calicoK', '#f6f1e8', '#3a302c', scale=3.0, lo=.62, hi=.64, rough=.85, seed=9)
    sphere((0, 0, .3), (1.0, .82, .42), body, 48)
    sphere((-.2, .2, .55), (.55, .4, .2), blk, 32)       # black patch on the back
    hy = -.35 if not awake else -.55
    sphere((.5, hy, .55 if not awake else .75), (.5, .46, .36), mat('catface', '#f8f4ec', .85, .1), 40)
    sphere((.32, hy + .12, .78 if not awake else .98), (.2, .17, .1), mat('ear', '#e39a4a', .8, .1), 24)   # orange patch over one eye
    for sx in (-1, 1):
        cone((.5 + sx * .28, hy + .26, .82 if not awake else 1.02), .15, .0, .28, mat('ear', '#e39a4a' if sx < 0 else '#3a302c', .8, .1), 16, rot=(math.radians(-35), sx * math.radians(20), 0))
    tc = mat('tailc', '#e39a4a', .8, .1)
    for i in range(30):   # tail curling round the front, as a chain of overlapping soft spheres
        u = i / 29; ang = math.radians(165 + u * 115); r = .95 - u * .08
        sphere((math.cos(ang) * r, math.sin(ang) * r * .82, .3 + u * .05), (.17, .17, .15), tc if u < .85 else mat('cw2', '#3a302c', .85, .1), 20)
    ink = mat('ink', '#2a1a12', 1.0, 0.0)
    ez = .86 if not awake else 1.06; ey = hy - .2
    for sx in (-1, 1):
        if awake:
            sphere((.5 + sx * .17, ey - .02, ez), (.07, .05, .06), ink, 20)
        else:
            bpy.ops.mesh.primitive_torus_add(major_radius=.06, minor_radius=.014, major_segments=24, minor_segments=8, location=(.5 + sx * .16, ey, ez))
            t = bpy.context.object; t.data.materials.append(ink)
            bm_ = bmesh.new(); bm_.from_mesh(t.data)
            bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.y > -0.01], context='VERTS'); bm_.to_mesh(t.data); bm_.free()
    sphere((.5, ey - .1, ez - .14), (.2, .14, .12), mat('muz', '#fbf7f0', .8, .1), 24)
    sphere((.5, ey - .17, ez - .05), (.035, .025, .02), mat('nose', '#e89a9a', .8, .05), 16)
    fit_render(sc, 'cat_awake' if awake else 'cat', px=110)

def nut(kind):
    sc = reset(); top_light(sc)
    if kind == 'donguri':
        sphere((0, -.1, .25), (.24, .34, .24), mat('acorn', '#a8682e', .3, .45), 40)
        cap = noise_mat('cap', '#6e5332', '#8a6c44', 40, .9, .8)
        sphere((0, .2, .28), (.27, .16, .25), cap, 32)
        cyl((0, .38, .3), .03, .14, mat('stalk', '#5a4228', .8, .1), 12, (math.radians(90), 0, 0))
    elif kind == 'kuri':
        o = sphere((0, 0, .25), (.42, .4, .22), mat('kuri', '#6a3518', .25, .5), 48)
        for v in o.data.vertices:
            if v.co.y > 0: v.co.x *= 1 - v.co.y * .55
        sphere((0, -.33, .2), (.36, .1, .16), noise_mat('kuribase', '#c8a070', '#d8b888', 30, .9, .4), 32)
        cone((0, .45, .28), .05, 0, .14, mat('kuritip', '#d8c09a', .9, .1), 12, (math.radians(-90), 0, 0))
    else:   # matsubokkuri (pine cone)
        sc_m = noise_mat('cone', '#7a5634', '#93693e', 20, .85, .5)
        for ring in range(9):
            z = ring / 8; r = .32 * math.sin(math.pi * (0.15 + z * .8)); n = 7 + ring % 2
            for k in range(n):
                a = k / n * math.tau + ring * .4
                sphere((math.cos(a) * r, -.45 + z * .9, .2 + math.sin(a) * r * .5 + .12), (.1, .09, .05), sc_m, 12, (0, 0, a))
    fit_render(sc, kind, px=PX)

def branch():
    """Persimmon branch reaching in from the top-right corner, with ripe kaki and leaves."""
    sc = reset(); top_light(sc)
    bark = noise_mat('bark', '#4a3324', '#5c4030', 12, .9, .6)
    pts = [(4.2, 6.9, 1.5), (3.2, 6.1, 1.6), (2.1, 5.6, 1.65), (1.0, 5.4, 1.7)]
    cu = bpy.data.curves.new('br', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .09; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for j, p in enumerate(pts): sp.points[j].co = (*p, 1); sp.points[j].radius = 1.6 - j * .35
    ob = bpy.data.objects.new('br', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(bark)
    for (a, b) in (((2.9, 6.0, 1.6), (2.4, 4.9, 1.6)), ((1.9, 5.6, 1.65), (1.3, 6.4, 1.6)), ((3.6, 6.4, 1.55), (3.9, 5.4, 1.5))):
        vein(a, b, .04, bark)
    kaki = mat('kakif', '#e8761e', .35, .4, .1)
    calyx = mat('calyx', '#5a6a2a', .8, .1)
    for (x, y) in ((2.4, 4.75), (1.25, 6.5), (3.95, 5.25)):
        o = sphere((x, y, 1.4), (.36, .36, .3), kaki, 48)
        for k in range(4):
            a = k * math.pi / 2 + .4; sphere((x + math.cos(a) * .1, y + math.sin(a) * .1, 1.71), (.13, .07, .03), calyx, 12, (0, 0, a))
    lm = mottle('kakileaf', '#c45a26', '#d98a2e', '#6d6a22')
    random.seed(12)
    for (x, y, a) in ((1.0, 5.1, -2.5), (1.6, 5.9, 2.2), (2.7, 5.2, -2.0), (3.3, 5.7, -1.2), (2.2, 6.3, 1.6), (3.9, 6.7, .4), (0.7, 5.8, 2.8), (4.3, 5.9, -.6)):
        pts2 = []
        for i in range(30):
            t = i / 30 * math.tau; pts2.append((math.sin(t) * .3 * (1 - .25 * math.cos(t)), -math.cos(t) * .55))
        o = flat_shape('kl', pts2, lm, .3, .04); o.location = (x, y, 1.75 + random.uniform(0, .1)); o.rotation_euler = (random.uniform(-.2, .2), random.uniform(-.2, .2), a)
    fit_render(sc, 'branch', px=100)

def imo(baked=False):
    sc = reset(); top_light(sc)
    skin = noise_mat('imoskin', '#8a2a3e', '#a8364a', 6, .55, .3)
    def tuber(x, y, a, L=1.0, r=.3, cut=False):
        o = sphere((x, y, .3), (L * .62, r, r * .9), skin, 48, (0, 0, a))
        for v in o.data.vertices:
            k = abs(v.co.x); v.co.y *= 1 - .45 * k * k; v.co.z *= 1 - .45 * k * k
        return o
    if not baked:
        tuber(0, 0, .2); tuber(.1, .55, -.15, .9, .27)
    else:
        burnt = noise_mat('burnt', '#4a1e22', '#7a2a36', 9, .8, .6, .45, .62)
        gold = noise_mat('gold', '#f0a830', '#f8cc58', 14, .45, .25)
        for k, (dy, a) in enumerate(((.3, .12), (-.3, -.1))):   # two halves, cut faces up
            o = tuber(0, dy, a, 1.1, .33); o.data.materials[0] = burnt; o.scale.z *= .5; o.location.z = .12
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, dy, .27)); f = bpy.context.object
            f.rotation_euler.z = a; f.scale = (.62, .27, .02); f.data.materials.append(gold); smooth(f)
            for v in f.data.vertices:
                kx = abs(v.co.x); v.co.y *= 1 - .45 * kx * kx
    fit_render(sc, 'yakiimo' if baked else 'imo', px=PX)

def bg():
    """Full-frame top view of an autumn garden: veranda at the top, moss + soil, stepping stones, lantern, fire pit."""
    sc = reset(); top_light(sc); sc.render.film_transparent = False
    W, H = 7.2, 12.8
    ground = noise_mat('soil', '#7a6248', '#8c7456', 3, .95, .3)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=100, size=1, location=(0, 0, 0)); g = bpy.context.object; g.scale = (W + 2, H + 2, 1)
    bpy.ops.object.transform_apply(scale=True); g.data.materials.append(ground); displace(g, .05, .5, 1)
    moss = noise_mat('moss', '#5b7a3a', '#76924a', 8, .95, .5)
    random.seed(7)
    for i in range(26):   # moss cushions along the sides
        side = -1 if i % 2 else 1
        x = side * random.uniform(2.3, 3.9); y = random.uniform(-6.2, 4.8)
        o = sphere((x, y, -.05), (random.uniform(.6, 1.1), random.uniform(.6, 1.2), .12), moss, 24); displace(o, .05, .2, 1)
    stone = noise_mat('stone', '#8f8b84', '#a8a39a', 4, .8, .5)
    for (x, y, s) in ((0.2, 4.2, .55), (-0.5, 2.6, .5), (0.3, 1.0, .52), (-0.4, -0.6, .5), (0.25, -2.1, .48)):
        o = cyl_flat((x, y, .03), s, .1, stone, 48, .04); o.scale = (1.1, .85, 1); o.rotation_euler.z = random.uniform(0, 3)
    # veranda (engawa) at the top with a dark shadow under the eaves
    wood = noise_mat('engawa', '#8a6646', '#9c7654', 2, .55, .1)
    for k in range(6): box((0, 5.75 + k * .2, .3), (W + 2, .19, .08), wood, .01, 2)
    box((0, 5.62, .2), (W + 2, .08, .3), mat('engawa_e', '#6a4a32', .6, .1), .01, 2)
    for x in (-3.0, 0.0, 3.0): box((x, 5.7, .15), (.22, .22, .3), mat('post', '#5a3e2a', .6, .1), .02, 2)
    # stone lantern (top view: hex cap with a jewel), left middle
    lan = noise_mat('lantern', '#9a958c', '#b0aba0', 5, .85, .4)
    cyl_flat((-2.5, 1.9, .2), .55, .2, lan, 6, .05); cyl_flat((-2.5, 1.9, .8), .75, .16, lan, 6, .08)
    sphere((-2.5, 1.9, 1.0), (.18, .18, .14), lan, 24)
    # shrubs (azalea) right side
    sh = noise_mat('shrub', '#3e5e2e', '#55743a', 14, .9, .7)
    for (x, y, r) in ((3.1, 2.4, .9), (2.7, 3.3, .7), (3.3, -1.0, .8)):
        o = sphere((x, y, .3), (r, r, .45), sh, 32); displace(o, .12, .15, 2)
    # fire pit: a ring of stones round an ash bed (the place to gather the leaves), lower middle
    FX, FY, FR = 0.6, -4.0, 1.25
    ash = noise_mat('ash', '#8e8780', '#a39c94', 10, .95, .3)
    cyl_flat((FX, FY, .0), FR, .04, ash, 64, .02)
    random.seed(2)
    for k in range(13):
        a = k / 13 * math.tau; o = sphere((FX + math.cos(a) * (FR + .08), FY + math.sin(a) * (FR + .08), .08), (.24, .2, .14), stone, 20, (0, 0, a)); displace(o, .03, .1, 1)
    char = mat('char', '#2a2422', .9, .05)
    for k in range(7): sphere((FX + random.uniform(-.6, .6), FY + random.uniform(-.5, .5), .04), (.12, .05, .04), char, 10, (0, 0, random.uniform(0, 3)))
    # straw mat with sweet potatoes waiting, bottom-left
    straw = noise_mat('straw', '#c8aa6a', '#dcc082', 40, .9, .4)
    box((-2.2, -5.0, .02), (1.9, 1.3, .04), straw, .02, 2)
    skin = noise_mat('imoskin', '#8a2a3e', '#a8364a', 6, .55, .3)
    for (x, y, a) in ((-2.6, -5.1, .3), (-1.9, -4.8, -.2), (-2.2, -5.35, .1)):
        o = sphere((x, y, .2), (.5, .2, .17), skin, 32, (0, 0, a))
    # a few fallen kaki leaves and twigs baked into the ground for texture (not part of the game leaves)
    cam_top(sc, -W / 2, W / 2, -H / 2, H / 2, 100)
    sc.render.filepath = os.path.join(OUT, 'bg.png'); bpy.ops.render.render(write_still=True); print('wrote bg', flush=True)
    META['fire'] = {'x': FX, 'y': FY, 'r': FR}; META['stones'] = [[0.2, 4.2, .55], [-0.5, 2.6, .5], [0.3, 1.0, .52], [-0.4, -0.6, .5], [0.25, -2.1, .48]]
    json.dump(META, open(META_PATH, 'w'), indent=1)

JOBS = {'bg': bg, 'broom': broom, 'cat': cat, 'cat_awake': lambda: cat(True), 'branch': branch, 'imo': imo, 'yakiimo': lambda: imo(True)}
for k in LEAVES: JOBS[k] = (lambda k=k: leaf(k))
for k in ('donguri', 'kuri', 'matsu'): JOBS[k] = (lambda k=k: nut(k))
for name, fn in JOBS.items():
    if WHAT in ('all', name) or name in WHAT.split(','): fn()
