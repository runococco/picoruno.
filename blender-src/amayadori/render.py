# Renders the sprites for amayadori.html: the walking cat poses, the umbrella and the roadside props
# (side view, anchors recorded in scene.json). The street itself is drawn by the game so it can scroll.
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 6.0; TZ = 3.0      # room: camera almost level, ortho height 8 units centred at z=3
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#e8eef6'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # soft overcast rainy-day light from above + cool fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.6; s.data.angle = math.radians(60); s.data.color = srgb('#eef4ff')
    s.rotation_euler = Euler((math.radians(25), math.radians(-20), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 700; a.data.size = 8; a.data.color = srgb('#e8f0ff')
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
def side_cam(sc, scale, res, tz, tx=0.0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    loc = Vector((tx, -30, tz)); bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + (x - tx) * res / scale, 1), round(res / 2 - (z - tz) * res / scale, 1)]

def leg(x, z0, ang, m, r=0.055, L=0.26):
    """a leg hanging from (x, z0) swung by ang (radians, + = forward)"""
    cx = x + math.sin(ang) * L / 2; cz = z0 - math.cos(ang) * L / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=L, location=(cx, -0.08, cz)); o = bpy.context.object
    o.rotation_euler = (0, ang, 0); o.data.materials.append(m); smooth(o)
    sphere((x + math.sin(ang) * L, -0.08, z0 - math.cos(ang) * L), (r * 1.15, r * 1.15, r * 0.8), m, 16)

def build_cat(name, legs, body_lift=0.0, tail_up=1.0, wet=False):
    sc = reset(True)
    wh = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); og = mat('cato', '#e8a050', 0.85, 0.1); pk = mat('catpk', '#f4a8a0', 0.8); bk = mat('eye', '#1a1210', 0.9)
    z = 0.42 + body_lift
    sphere((0, 0, z), (0.36, 0.2, 0.2), wh, 48)
    sphere((-0.1, -0.02, z + 0.08), (0.16, 0.16, 0.1), og, 24)
    sphere((0.38, 0, z + 0.2), (0.19, 0.17, 0.17), wh, 48)                     # head
    sphere((0.33, -0.05, z + 0.3), (0.09, 0.08, 0.06), og, 16)
    for dy in (-0.07, 0.07):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.06, depth=0.12, location=(0.36 + (0.02 if dy < 0 else -0.02), dy, z + 0.38)); e = bpy.context.object
        e.rotation_euler = (0, -0.25, 0); e.data.materials.append(og if dy > 0 else wh); smooth(e)
    sphere((0.47, -0.14, z + 0.24), (0.03, 0.014, 0.034), bk, 12)                # dot eye (side view)
    sphere((0.565, -0.02, z + 0.17), (0.018, 0.015, 0.014), pk, 8)              # nose
    sphere((0.45, -0.15, z + 0.16), (0.032, 0.01, 0.018), pk, 8)                  # cheek
    for (lx, a, near) in legs:   # (x, swing angle, near side?)
        leg(lx, z - 0.08, a, wh if near else mat('catw2', '#e8e0d0', 0.85, 0.1))
        if not near: bpy.context.object.location.y += 0.16
    # tail: curve up
    pts = [(-0.34, 0, z), (-0.5, 0, z + 0.12 * tail_up), (-0.52, 0, z + 0.32 * tail_up), (-0.44, 0, z + 0.44 * tail_up)]
    cu = bpy.data.curves.new('tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.04; cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for p_, q in zip(sp.bezier_points, pts): p_.co = q; p_.handle_left_type = p_.handle_right_type = 'AUTO'
    t = bpy.data.objects.new('tail', cu); sc.collection.objects.link(t); cu.materials.append(og)
    if wet:   # droplets on the fur
        dr = mat('drop', '#a8d0f0', 0.05, 0.8)
        for (dx, dz) in ((0.1, 0.62), (-0.15, 0.6), (0.4, 0.82), (0.25, 0.55)): sphere((dx, -0.21, dz + body_lift), (0.025, 0.01, 0.032), dr, 12)
    to2d = side_cam(sc, 1.6, 256, 0.55)
    SPR['cat'] = {'res': 256, 'pxu': 256 / 1.6, 'feet': to2d(0.0, 0.0), 'head': to2d(0.4, z + 0.25)}
    render(sc, name)

def build_cats():
    near, far = True, False
    build_cat('cat_w0', [(0.22, 0.35, near), (0.22, -0.25, far), (-0.22, -0.3, near), (-0.22, 0.3, far)])
    build_cat('cat_w1', [(0.22, -0.25, near), (0.22, 0.35, far), (-0.22, 0.3, near), (-0.22, -0.3, far)])
    build_cat('cat_jump', [(0.22, 0.9, near), (0.22, 0.75, far), (-0.22, -0.9, near), (-0.22, -0.75, far)], 0.08, 0.6)
    build_cat('cat_wet', [(0.22, 0.05, near), (0.22, -0.05, far), (-0.22, 0.05, near), (-0.22, -0.05, far)], -0.04, 0.3, True)

def build_umbrella():
    sc = reset(True)
    cols = [mat('umb0', '#5aa8e8', 0.55, 0.2), mat('umb1', '#f6f0e0', 0.55, 0.2)]
    # 8 panels of a shallow canopy, alternating colours, + ribs and a crook handle
    n = 8; R = 0.75; H = 0.32
    for k in range(n):
        bm = bmesh.new(); a0 = k / n * math.tau; a1 = (k + 1) / n * math.tau
        top = bm.verts.new((0, 0, H)); rows = []
        for j in range(1, 9):
            f = j / 8; r = R * f; zz = H * (1 - f ** 1.6)
            rows.append([bm.verts.new((math.cos(a0 + (a1 - a0) * i / 6) * r, math.sin(a0 + (a1 - a0) * i / 6) * r, zz)) for i in range(7)])
        for i in range(6): bm.faces.new((top, rows[0][i], rows[0][i + 1]))
        for j in range(7):
            for i in range(6): bm.faces.new((rows[j][i], rows[j + 1][i], rows[j + 1][i + 1], rows[j][i + 1]))
        me = bpy.data.meshes.new(f'p{k}'); bm.to_mesh(me); me.materials.append(cols[k % 2])
        o = bpy.data.objects.new(f'p{k}', me); sc.collection.objects.link(o); smooth(o)
        so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = 0.01
    rib = mat('rib', '#4a3a3a', 0.5, 0.3)
    for k in range(n):
        a = k / n * math.tau; sphere((math.cos(a) * R, math.sin(a) * R, 0.0), (0.025, 0.025, 0.025), rib, 8)
    sphere((0, 0, H + 0.04), (0.03, 0.03, 0.06), rib, 12)
    hd = wood('handle', '#a86a3a', '#8a522a')
    cyl((0, 0, -0.35), 0.018, 1.3, rib, 12)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.025, location=(0.08, 0, -1.0)); t = bpy.context.object; t.rotation_euler = (math.radians(90), 0, 0); t.data.materials.append(hd)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in t.data.vertices: v.select = v.co.z > 0.01
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    to2d = side_cam(sc, 2.0, 320, -0.25)
    SPR['umb'] = {'res': 320, 'pxu': 160, 'grip': to2d(0, -0.8), 'R': R, 'top': to2d(0, H), 'rim': to2d(R, 0)}
    render(sc, 'umb')

def build_props():
    # hydrangea bush
    sc = reset(True); random.seed(2)
    lf = mat('leaf', '#4a8a4a', 0.7); cols = [mat(f'hy{i}', c, 0.7, 0.1) for i, c in enumerate(['#7a9ae8', '#9a8ae0', '#b8a0e8', '#88b8f0'])]
    for k in range(9):
        a = random.random() * math.tau; sphere((math.cos(a) * 0.5, 0.1 + math.sin(a) * 0.15, 0.25 + random.random() * 0.2), (0.25, 0.08, 0.14), lf, 16, (0, 0, a))
    for k, (x, z, r) in enumerate(((-0.35, 0.55, 0.24), (0.0, 0.7, 0.28), (0.36, 0.52, 0.23), (-0.15, 0.38, 0.2), (0.2, 0.36, 0.2))):
        m = cols[k % 4]
        for j in range(70):
            u = random.random() * math.tau; v = random.random() * math.pi; rr = r * random.random() ** 0.3
            p = (x + math.cos(u) * math.sin(v) * rr, -0.15 + math.sin(u) * math.sin(v) * rr * 0.7, z + math.cos(v) * rr * 0.9)
            sphere(p, (0.05, 0.03, 0.05), m, 8)
    side_cam(sc, 1.6, 256, 0.55); SPR['ajisai'] = {'res': 256, 'pxu': 160, 'base': [128.0, 128 + 0.55 * 160]}
    render(sc, 'ajisai')
    # stone lantern
    sc = reset(True); st = noise_mat('stone', '#9a958a', '#b0aa9c', 6, 0.9, 0.6)
    cyl((0, 0, 0.05), 0.2, 0.1, st, 24); cyl((0, 0, 0.35), 0.06, 0.5, st, 16); bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.7)); o = bpy.context.object; o.scale = (0.26, 0.26, 0.22); o.data.materials.append(st)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.3, depth=0.18, location=(0, 0, 0.9)); o = bpy.context.object; o.rotation_euler = (0, 0, math.radians(45)); o.data.materials.append(st)
    sphere((0, 0, 1.01), (0.05, 0.05, 0.05), st, 12)
    side_cam(sc, 1.6, 256, 0.55); SPR['toro'] = {'res': 256, 'pxu': 160, 'base': [128.0, 128 + 0.55 * 160]}
    render(sc, 'toro')
    # snail on a leaf
    sc = reset(True); sh = mat('shell', '#c8905a', 0.5, 0.3); bd = mat('slug', '#d8c8a8', 0.6, 0.3, sss=0.2)
    sphere((0, 0, 0.05), (0.2, 0.06, 0.05), bd, 24); sphere((0.18, 0, 0.12), (0.04, 0.04, 0.07), bd, 16)
    for s_ in (-1, 1): cyl((0.2, s_ * 0.02, 0.22), 0.008, 0.1, bd, 8, (0, 0.3, 0)); sphere((0.215, s_ * 0.02, 0.27), (0.016, 0.016, 0.016), mat('se', '#1a1210', 0.9), 8)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.06, location=(-0.03, 0, 0.16)); t = bpy.context.object; t.rotation_euler = (math.radians(90), 0, 0); t.data.materials.append(sh)
    sphere((-0.03, -0.02, 0.16), (0.1, 0.05, 0.1), sh, 24)
    side_cam(sc, 0.8, 128, 0.15); SPR['snail'] = {'res': 128, 'pxu': 160, 'base': [64.0, 64 + 0.15 * 160]}
    render(sc, 'snail')

JOBS = {'cats': build_cats, 'umb': build_umbrella, 'props': build_props}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
