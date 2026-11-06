# Renders the layers for tombo.html. Every layer is rendered with the SAME full-frame camera
# (720x1280, 80 px per unit) so the game can stack them; build.py crops each to its bounding box.
# python3 render.py <what> <outdir>      what = all | bg,usu,mochi,usagi,kine,turner,plate (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 8.0; TZ = 3.2      # camera: ortho height 9.5 units, target (0,0,TZ)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#f2b27a'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
    # moonlight key from upper right + warm lantern fill from the left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.0; s.data.angle = math.radians(20); s.data.color = srgb('#ffc890')
    s.rotation_euler = Euler((math.radians(55), math.radians(-35), math.radians(160)))
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 4))
    a = bpy.context.object; a.data.energy = 700; a.data.size = 6; a.data.color = srgb('#ffe2c8')
    a.rotation_euler = (Vector((0, 0, 1.5)) - a.location).to_track_quat('-Z', 'Y').to_euler()
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

# ---------------------------------------------------------------- sprite camera (close-up props, rendered separately)
SPR_META = {}
def sprite_cam(sc, scale, res, elev=38, az=0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    e = math.radians(elev); a = math.radians(az); d = 30
    loc = Vector((math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (-loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    bpy.context.view_layer.update()
    sc.render.resolution_x = sc.render.resolution_y = res
    return lambda p: (res / 2 + (Vector(p) @ c.matrix_world.to_3x3().col[0]) * res / scale,
                      res / 2 - (Vector(p) @ c.matrix_world.to_3x3().col[1]) * res / scale)

def wing_mat(name, tint, base=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    out = nt.nodes['Material Output']; pb = nt.nodes['Principled BSDF']
    pb.inputs['Base Color'].default_value = (*srgb(tint), 1); pb.inputs['Roughness'].default_value = 0.15; pb.inputs['Specular IOR Level'].default_value = 0.8
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 26
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[1].position = 0.06
    rp.color_ramp.elements[0].color = (0.75, 0.75, 0.75, 1); rp.color_ramp.elements[1].color = (0.32, 0.32, 0.32, 1)   # veins opaque-ish
    nt.links.new(vo.outputs['Distance'], rp.inputs['Fac'])
    fac = rp.outputs['Color']
    if base:   # amber patch near the wing root (akatombo)
        gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4, 4, 4)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'LIGHTEN'; mx.inputs[0].default_value = 1
        nt.links.new(fac, mx.inputs[6]); nt.links.new(gr.outputs['Fac'], mx.inputs[7]); fac = mx.outputs[2]
        cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.inputs[6].default_value = (*srgb(tint), 1); cm.inputs[7].default_value = (*srgb(base), 1)
        nt.links.new(gr.outputs['Fac'], cm.inputs[0]); nt.links.new(cm.outputs[2], pb.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(fac, sep.inputs[0])
    nt.links.new(sep.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(pb.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m

SPECIES = {   # abdomen, abdomen tip, thorax, eyes, wing tint, wing base, size
    'aka': ('#d8331f', '#c42a1a', '#a8502a', '#9a3a24', '#f6efe0', '#f0b45a', 1.0),
    'shiokara': ('#9fbcd8', '#2a2a2a', '#3e3a36', '#3a6a8a', '#f2f2f2', None, 1.05),
    'oniyanma': ('#2a2622', '#2a2622', '#2e3a26', '#3aa060', '#f4f0e0', None, 1.45),
}

def dragonfly(kind, pose):
    ab, tip, th, ey, wt, wb, sz = SPECIES[kind]
    am = mat('ab_' + kind, ab, 0.4, 0.4); tm = mat('tip_' + kind, tip, 0.4, 0.4); hm = mat('th_' + kind, th, 0.5, 0.3)
    em = mat('eye_' + kind, ey, 0.15, 0.7); band = mat('band', '#e8c832', 0.4, 0.3)
    root = bpy.data.objects.new('df', None); bpy.context.collection.objects.link(root)
    def P(o): o.parent = root; return o
    P(sphere((0.34, 0, 0), (0.17, 0.12, 0.13), hm, 32))                     # thorax
    P(sphere((0.52, 0, 0.01), (0.08, 0.11, 0.09), hm, 24))                  # head
    dot = mat('dot', '#14100c', 0.2, 0.5)
    for s in (-1, 1):
        P(sphere((0.57, s * 0.08, 0.05), (0.09, 0.085, 0.095), em, 32))    # big compound eyes
        P(sphere((0.6, s * 0.095, 0.115), (0.028, 0.028, 0.028), dot, 16))  # solid dot pupil on top
    for i in range(10):                                                     # abdomen segments
        u = i / 9; x = 0.2 - u * 0.78; r = 0.07 - 0.022 * u
        mm = tm if (u > 0.8 and kind == 'shiokara') else (band if (kind == 'oniyanma' and i % 2 == 1) else am)
        P(sphere((x, 0, -0.01 - u * 0.02), (0.06, r, r), mm, 16))
    for s in (-1, 1):                                                        # anal appendages
        P(cyl((-0.62, s * 0.012, -0.03), 0.006, 0.08, tm, 6, (0, math.radians(90), 0)))
    leg = mat('leg', '#2a201a', 0.6, 0.2)
    for i, dx in enumerate((0.42, 0.36, 0.3)):
        for s in (-1, 1):
            P(cyl((dx, s * 0.06, -0.12), 0.008, 0.18, leg, 6, (s * math.radians(25), math.radians(-15 + i * 15), 0)))
    wm = wing_mat('wing_' + kind, wt, wb)
    lift = {'perch': -8, 'up': 40, 'down': -30}[pose]
    for (x0, L, W) in ((0.44, 0.7, 0.12), (0.27, 0.66, 0.16)):
        for s in (-1, 1):
            pts = []
            for k in range(24):
                t = k / 24 * math.tau; pts.append((math.sin(t) * W * (1 - 0.3 * math.cos(t)), (1 - math.cos(t)) / 2 * L))
            me = bpy.data.meshes.new('w'); bm = bmesh.new(); c0 = bm.verts.new((0, 0.0, 0)); vs = [bm.verts.new((px, py, 0)) for px, py in pts]
            for k in range(len(vs)): bm.faces.new((c0, vs[k], vs[(k + 1) % len(vs)]))
            bm.to_mesh(me); bm.free()
            w = bpy.data.objects.new('w', me); bpy.context.collection.objects.link(w); w.data.materials.append(wm)
            w.location = (x0, s * 0.05, 0.08); w.rotation_euler = (s * math.radians(lift) * -1 if s > 0 else math.radians(lift), 0, 0)
            w.rotation_euler = Euler((math.radians(-lift) * s, 0, math.radians(30 if x0 > 0.35 else -24) * s))
            if s < 0: w.scale = (1, -1, 1)
            P(w)
    root.scale = (sz, sz, sz)
    return root

def build_dragonfly(kind, pose):
    sc = reset(); sc.render.film_transparent = True
    dragonfly(kind, pose)
    to2d = sprite_cam(sc, 1.75 * SPECIES[kind][6], 300, elev=55, az=0)
    s = SPECIES[kind][6]
    name = f'df_{kind}_{pose}'
    SPR_META[name] = {'res': 300, 'feet': to2d((0.36 * s, 0, -0.2 * s)), 'eye': to2d((0.6 * s, -0.095 * s, 0.115 * s)), 'eye2': to2d((0.6 * s, 0.095 * s, 0.115 * s)), 'head': to2d((0.5 * s, 0, 0.02 * s))}
    render(sc, name)

def build_foxtail():
    sc = reset(); sc.render.film_transparent = True
    stem = mat('fstem', '#7a9a3a', 0.6, 0.1)
    pts = [Vector((0, 0, -2.6)), Vector((0.08, 0, -1.4)), Vector((0.02, 0, -0.35))]
    cu = bpy.data.curves.new('st', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.025; sp = cu.splines.new('NURBS'); sp.points.add(2); sp.use_endpoint_u = True
    for j, p in enumerate(pts): sp.points[j].co = (*p, 1)
    ob = bpy.data.objects.new('st', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(stem)
    core = mat('fcore', '#a8b860', 0.7, 0.1); hair = mat('fhair', '#d8d890', 0.6, 0.2, sss=0.3)
    random.seed(4)
    for i in range(70):
        u = i / 69; z = -0.35 + u * 0.75; r = 0.07 * math.sin(math.pi * (0.1 + u * 0.85)) + 0.02
        sphere((0.02 + 0.06 * u * u, 0, z), (r, r, 0.06), core, 12)
        for k in range(5):
            a = random.random() * math.tau; L = 0.12 + random.random() * 0.06
            base = Vector((0.02 + 0.06 * u * u + math.cos(a) * r, math.sin(a) * r, z)); d = Vector((math.cos(a), math.sin(a), 0.6)).normalized()
            bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.004, depth=L, location=base + d * L / 2)
            h = bpy.context.object; h.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); h.data.materials.append(hair)
    to2d = sprite_cam(sc, 3.4, 340, elev=10, az=0)
    SPR_META['foxtail'] = {'res': 340, 'tip': to2d((0.08, 0, 0.42)), 'mid': to2d((0.05, 0, 0.05))}
    render(sc, 'foxtail')

def build_cage():
    sc = reset(); sc.render.film_transparent = True
    g = mat('cage', '#5aa84a', 0.4, 0.3); lid = mat('lid', '#e88a2a', 0.4, 0.3)
    for (x, y) in ((-0.5, -0.32), (0.5, -0.32), (-0.5, 0.32), (0.5, 0.32)):
        cyl((x, y, 0.35), 0.03, 0.7, g, 8)
    for z in (0.02, 0.68):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z)); b = bpy.context.object; b.scale = (1.06, 0.7, 0.06); b.data.materials.append(g if z < .5 else lid); bevel(b, 0.02)
    for i in range(1, 12):
        x = -0.5 + i / 12
        cyl((x, -0.32, 0.35), 0.008, 0.66, g, 6); cyl((x, 0.32, 0.35), 0.008, 0.66, g, 6)
    for i in range(1, 8):
        y = -0.32 + i / 8 * 0.64; cyl((-0.5, y, 0.35), 0.008, 0.66, g, 6); cyl((0.5, y, 0.35), 0.008, 0.66, g, 6)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.025, location=(0, 0, 0.78), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(lid)
    sprite_cam(sc, 1.6, 220, elev=25, az=20)
    render(sc, 'cage')

PERCH = [(-1.55, -0.8, 2.7), (1.45, -0.8, 3.3), (0.15, -1.2, 2.05), (-0.6, -0.4, 4.7)]
def build_bg():
    sc = reset(False)
    w = sc.world; nt = w.node_tree; bg = nt.nodes['Background']; bg.inputs[1].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Window'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs[1], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (*srgb('#f7b26a'), 1)
    e2 = ramp.color_ramp.elements.new(0.7); e2.color = (*srgb('#e98a6e'), 1)
    ramp.color_ramp.elements[-1].position = 1.0; ramp.color_ramp.elements[-1].color = (*srgb('#7a6a9e'), 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    # low sun behind the far hills
    sun = mat('sundisc', '#ffb860', 1.0, 0.0, emit=('#ffc070', 1.0))
    sphere((1.2, 30, zfor(560, 30)), (0.75, 0.05, 0.75), sun, 48)
    # hill layers
    for (y, col, h, seed) in ((26, '#9a6a8a', 1.0, 1), (20, '#7a5a7a', 1.3, 2), (14, '#5e4a62', 1.1, 3)):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=2, size=1, location=(0, y, 0)); g = bpy.context.object; g.scale = (14, 0.5, 1)
        bpy.ops.object.transform_apply(scale=True)
        random.seed(seed); ph = random.random() * 6
        for v in g.data.vertices:
            if v.co.y > 0: v.co.z = zfor(600, y) - 3.2 + h * (0.6 + 0.4 * math.sin(v.co.x * 0.7 + ph) + 0.25 * math.sin(v.co.x * 1.9 + ph * 2))
            else: v.co.z = -2
        g.rotation_euler.x = math.radians(90); g.location = (0, y, 0)
        for v in g.data.vertices: pass
        g.data.materials.append(mat('hill' + str(y), col, 0.95, 0.0))
    # rice field with drying racks (hazakake)
    field = noise_mat('field', '#c99a4a', '#d8ac5a', 4, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, 0)); p = bpy.context.object; p.scale = (16, 14, 1); p.data.materials.append(field)
    rack = mat('rack', '#6a4a34', 0.8, 0.1); straw = noise_mat('straw', '#b89040', '#e0bc6a', 30, 0.9, 0.5); random.seed(11)
    for (x0, y0, n) in ((-2.6, 8, 6), (1.0, 10, 7)):
        for k in range(n): cyl((x0 + k * 0.6, y0, 0.55), 0.03, 1.1, rack, 8)
        cyl((x0 + (n - 1) * 0.3, y0, 1.02), 0.025, (n - 1) * 0.6 + 0.2, rack, 8, (0, math.radians(90), 0))
        L = (n - 1) * 0.6
        for b in range(int(L / 0.13) + 1):
            bx = x0 + b * 0.13 + random.uniform(-.02, .02); hh = 0.5 + random.uniform(-.06, .08)
            for side in (-1, 1):
                bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.075, radius2=0.03, depth=hh, location=(bx, y0 + side * 0.06, 1.02 - hh / 2))
                c = bpy.context.object; c.rotation_euler = (side * 0.18, 0, 0); c.data.materials.append(straw)
    # ground strip in front + susuki clumps
    grass = noise_mat('grass', '#8a8a3a', '#a09a48', 8, 0.95, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4, 0.01)); g2 = bpy.context.object; g2.scale = (16, 12, 1); g2.data.materials.append(grass)
    stem = mat('susuki', '#b9a46a', 0.9); plume = noise_mat('plume', '#e8d2b0', '#f6e8d0', 60, 0.95, 0.6, sss=0) if False else noise_mat('plume', '#e2c9a2', '#f4e4c8', 60, 0.95, 0.6)
    random.seed(8)
    def strand(pts, r, m):
        cu = bpy.data.curves.new('s', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 3
        for j, p in enumerate(pts): sp.points[j].co = (*p, 1); sp.points[j].radius = 1 - 0.8 * j / (len(pts) - 1)
        ob = bpy.data.objects.new('s', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    for k in range(18):
        x = random.uniform(-3.2, 3.2); y = random.uniform(-2.0, 1.5); h = 1.0 + random.random() * 1.1; lean = random.uniform(-.35, .35)
        top = Vector((x + math.sin(lean) * h, y, h))
        strand([Vector((x, y, 0)), Vector((x + math.sin(lean) * h * .5, y, h * .5)), top], 0.018, stem)
        dirn = 1 if lean >= 0 else -1
        for f in range(16):
            u = f / 15; base = top - Vector((math.sin(lean) * .35 * u, 0, .35 * u))   # strands sprout along the top of the stem
            L = 0.38 + random.random() * 0.18 - 0.1 * u
            p1 = base + Vector((dirn * L * .35 + random.uniform(-.05, .05), random.uniform(-.08, .08), L * .55))
            p2 = base + Vector((dirn * L * .75 + random.uniform(-.06, .06), random.uniform(-.12, .12), L * .45 - .08))
            strand([base, p1, p2], 0.016, plume)
    # bamboo poles (perches)
    bam = noise_mat('bamboo', '#9a8a4a', '#b0a05c', 6, 0.5, 0.2); node = mat('node', '#7a6a3a', 0.6, 0.1)
    for (x, y, z) in PERCH[:3]:
        cyl((x, y, z / 2), 0.07, z, bam, 24)
        for k in range(1, int(z / 0.7) + 1): cyl((x, y, k * 0.7), 0.078, 0.04, node, 24)
        cyl((x, y, z + 0.005), 0.072, 0.01, mat('cut', '#d8c890', 0.7, 0.1), 24)
    # persimmon tree from the left with a long twig reaching right (4th perch at its tip)
    bark = noise_mat('bark', '#3a2a22', '#4a3428', 10, 0.9, 0.6)
    tw = [(-4.2, 0.2, 2.0), (-3.0, 0.0, 3.6), (-1.8, -0.3, 4.4), (PERCH[3][0], PERCH[3][1], PERCH[3][2] - 0.02)]
    cu = bpy.data.curves.new('br', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.07; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(tw) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for j, p in enumerate(tw): sp.points[j].co = (*p, 1); sp.points[j].radius = 3.0 - j * 0.85
    ob = bpy.data.objects.new('br', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(bark)
    cyl((-4.3, 0.3, 2.5), 0.32, 5.0, bark, 24)
    kaki = mat('kaki', '#e8761e', 0.35, 0.4)
    for (x, z) in ((-2.9, 3.1), (-2.2, 3.9), (-3.5, 4.4)):
        sphere((x, -0.2, z), (0.22, 0.22, 0.2), kaki, 32)
    lf = noise_mat('kakileaf', '#b8522a', '#d07a32', 6, 0.7, 0.2)
    random.seed(3)
    lf2 = noise_mat('kakileaf2', '#8a6a2a', '#a8842e', 6, 0.7, 0.2)
    for i in range(34):
        u = random.random(); bx = -4 + u * 2.6
        sphere((bx, random.uniform(-0.5, 0.4), 3.2 + u * 1.2 + random.uniform(-.5, .6)), (0.2, 0.035, 0.1), lf if i % 3 else lf2, 12, (random.uniform(-.6, .6), random.uniform(-.4, .4), random.random() * 3))
    render(sc, 'bg')

def only(fn, name):
    sc = reset(); fn(); render(sc, name)

JOBS = {'bg': build_bg, 'foxtail': build_foxtail, 'cage': build_cage}
for k in SPECIES:
    for p in ('perch', 'up', 'down'): JOBS[f'df_{k}_{p}'] = (lambda k=k, p=p: build_dragonfly(k, p))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update({'pxu': PXU, 'perch': [proj(*p) for p in PERCH], 'spr': {**meta.get('spr', {}), **SPR_META}})
json.dump(meta, open(MP, 'w'))
