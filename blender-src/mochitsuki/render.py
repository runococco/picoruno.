# Renders the layers for mochitsuki.html. Every layer is rendered with the SAME full-frame camera
# (720x1280, 80 px per unit) so the game can stack them; build.py crops each to its bounding box.
# python3 render.py <what> <outdir>      what = all | bg,usu,mochi,usagi,kine,turner,plate (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 9.5; ELEV = 24.0; TZ = 2.6      # camera: ortho height 9.5 units, target (0,0,TZ)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#3a4677'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    # moonlight key from upper right + warm lantern fill from the left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(18); s.data.color = srgb('#dfe6ff')
    s.rotation_euler = Euler((math.radians(45), math.radians(25), math.radians(20)))
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 4))
    a = bpy.context.object; a.data.energy = 900; a.data.size = 4; a.data.color = srgb('#ffcf96')
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
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True); print('wrote', name, flush=True)

def fur(name, color, belly=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(color), 1)
    b.inputs['Roughness'].default_value = 0.9; b.inputs['Specular IOR Level'].default_value = 0.08
    b.inputs['Sheen Weight'].default_value = 0.7; b.inputs['Sheen Roughness'].default_value = 0.45
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (0.6, 0.4, 0.3); b.inputs['Subsurface Scale'].default_value = 0.05
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 140; nz.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def dots_mat(name, base, dot, scale=18, size=0.2):
    """豆絞り: white cloth with small indigo dots"""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); v = nt.nodes.new('ShaderNodeTexVoronoi'); v.inputs['Scale'].default_value = scale
    v.inputs['Randomness'].default_value = 0.0
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = size
    nt.links.new(v.outputs['Distance'], lt.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs[6].default_value = (*srgb(base), 1); mx.inputs[7].default_value = (*srgb(dot), 1)
    nt.links.new(lt.outputs[0], mx.inputs[0]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95; b.inputs['Specular IOR Level'].default_value = 0.05
    b.inputs['Sheen Weight'].default_value = 0.3
    return m

def blob(name, parts, m, K=1.55, res=0.012):
    """one seamless metaball body from ellipsoids [(co, (sx, sy, sz)), ...] -> mesh"""
    mb = bpy.data.metaballs.new(name); mb.resolution = 0.03; mb.render_resolution = res; mb.threshold = 0.6
    mo = bpy.data.objects.new(name, mb); bpy.context.collection.objects.link(mo); mo.data.materials.append(m)
    for co, sz in parts:
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.co = co; e.radius = 1.0
        e.size_x, e.size_y, e.size_z = sz[0] * K, sz[1] * K, sz[2] * K
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT'); mo.select_set(True); bpy.context.view_layer.objects.active = mo
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object; smooth(o); return o

def capsule(a, b, r, m, name='arm'):
    """metaball capsule from point a to point b (world)"""
    a = Vector(a); b = Vector(b); d = b - a
    mb = bpy.data.metaballs.new(name); mb.resolution = 0.03; mb.render_resolution = 0.012; mb.threshold = 0.6
    mo = bpy.data.objects.new(name, mb); bpy.context.collection.objects.link(mo); mo.data.materials.append(m)
    e = mb.elements.new(); e.type = 'CAPSULE'; e.co = (a + b) / 2; e.radius = r * 1.5; e.size_x = d.length / 2
    e.rotation = d.to_track_quat('X', 'Z')
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT'); mo.select_set(True); bpy.context.view_layer.objects.active = mo
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object; smooth(o); return o

def holdout(objs):
    for o in objs: o.is_holdout = True

# ---------------------------------------------------------------- scene parts
USU = (0.0, 0.3, 0.0)          # mortar base centre
USU_TOP = 1.25                  # rim height
MOCHI_Z = 1.12
PIVOT = (-1.27, 0.2, 1.85)      # where rabbit A holds the mallet (kine is drawn at y PIVOT[1]-0.6)
KPIV = (PIVOT[0], PIVOT[1] - 0.6, PIVOT[2])

def build_usu():
    before = set(bpy.data.objects)
    m = wood('usu', '#8a5a3a', '#a8714a')
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.95, depth=USU_TOP, location=(USU[0], USU[1], USU_TOP / 2))
    o = bpy.context.object; o.data.materials.append(m); smooth(o)
    for v in o.data.vertices:   # waisted drum shape
        z = v.co.z / (USU_TOP / 2); k = 1 - 0.13 * (1 - z * z); v.co.x *= k; v.co.y *= k
    bevel(o, 0.06)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(USU[0], USU[1], USU_TOP + 0.05))
    cut = bpy.context.object; cut.scale = (0.72, 0.72, 0.5); cut.hide_render = True
    bo = o.modifiers.new('bool', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    # wet inside of the hollow
    inner = mat('usu_in', '#7a4c30', 0.35, 0.4)
    o.data.materials.append(inner)
    for ring_z in (0.25, 1.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.86 if ring_z < .5 else 0.9, minor_radius=0.035, location=(USU[0], USU[1], ring_z))
        t = bpy.context.object; t.data.materials.append(mat('band', '#3a3330', 0.6)); smooth(t)
    return list(set(bpy.data.objects) - before)

def build_mochi(state):
    """state 0 = steamed rice, 1 = half pounded, 2 = finished. Sits INSIDE the hollow; the mortar is a holdout."""
    holdout(build_usu())
    R, HZ = 0.66, [0.2, 0.24, 0.27][state]
    if state < 2:
        m = noise_mat('mochi%d' % state, '#ece5d4', '#fbf8f1', [30, 18][state], [0.7, 0.6][state], [0.8, 0.5][state])
        b = m.node_tree.nodes['Principled BSDF']; b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Scale'].default_value = 0.1
        o = sphere((USU[0], USU[1], MOCHI_Z), (R, R, HZ), m, 64)
        s = o.modifiers.new('s', 'SUBSURF'); s.levels = s.render_levels = 2
        t = bpy.data.textures.new('lump%d' % state, 'CLOUDS'); t.noise_scale = [0.07, 0.16][state]
        d = o.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = [0.05, 0.035][state]; d.texture_coords = 'OBJECT'
        # rice grains on top (lots for steamed rice, a few left after some pounding)
        g = mat('grain', '#fdfbf4', 0.5, 0.25, sss=0.4)
        random.seed(5 + state); N = [420, 45][state]
        for i in range(N):
            a = random.random() * math.tau; r = math.sqrt(random.random()) * R * 0.95
            x, y = USU[0] + math.cos(a) * r, USU[1] + math.sin(a) * r
            z = MOCHI_Z + HZ * math.sqrt(max(0, 1 - (r / R) ** 2)) - 0.005
            sphere((x, y, z), (0.05, 0.026, 0.026), g, 10, (random.uniform(-.5, .5), random.uniform(-.5, .5), random.random() * math.pi))
    else:
        m = mat('mochiS', '#fbf8f1', 0.32, 0.35, sss=0.45)
        o = sphere((USU[0], USU[1], MOCHI_Z), (R, R, HZ), m, 96)
        face(USU[0], USU[1] - 0.58, MOCHI_Z + 0.16, 1.15)

def face(x, y, z, s=1.0, ouch=False, happy=False):
    blk = mat('eye', '#1a120e', 1.0, 0.0); pnk = mat('cheek', '#f2a0a0', 1.0, 0.0)
    if callable(x):   # placement function onto a surface: face(fn, 0, 0, z, s)
        P = x
        for sx in (-1, 1):
            ex = sx * 0.085 * s
            if ouch:
                for k in (-1, 1):
                    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.014 * s, depth=0.09 * s, location=P(ex, z + k * 0.018 * s), rotation=(0, math.radians(90 + sx * k * 30), 0))
                    bpy.context.object.data.materials.append(blk)
            elif happy:
                for k in (-1, 1):
                    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.014 * s, depth=0.06 * s, location=P(ex + k * 0.02 * s, z), rotation=(0, math.radians(90 + k * 40), 0))
                    bpy.context.object.data.materials.append(blk)
            else:
                sphere(P(ex, z), (0.036 * s, 0.018, 0.036 * s), blk, 20)
            sphere(P(sx * 0.17 * s, z - 0.058 * s), (0.045 * s, 0.012, 0.026 * s), pnk, 16)
        return
    for sx in (-1, 1):
        if ouch:   # > <
            for k in (-1, 1):
                bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.014 * s, depth=0.09 * s, location=(x + sx * 0.085 * s, y, z + k * 0.018 * s), rotation=(0, math.radians(90 + sx * k * 30), 0))
                bpy.context.object.data.materials.append(blk)
        elif happy:   # ^ ^
            for k in (-1, 1):
                bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.014 * s, depth=0.06 * s, location=(x + sx * 0.085 * s + k * 0.02 * s, y, z), rotation=(0, math.radians(90 + k * 40), 0))
                bpy.context.object.data.materials.append(blk)
        else:
            sphere((x + sx * 0.085 * s, y, z), (0.036 * s, 0.018, 0.036 * s), blk, 20)
        sphere((x + sx * 0.16 * s, y + 0.006, z - 0.058 * s), (0.045 * s, 0.012, 0.026 * s), pnk, 16)

def rabbit(x, color, lean, pose='idle', name='r', coat='#2f4f8f', belt='#d9534a'):
    """Round chubby rabbit in a happi coat + 豆絞り headband. pose: hold / idle / reach / ouch / cheer.
    Returns (body objects, arm objects) so the arms can go to their own layer."""
    before = set(bpy.data.objects)
    body = fur('fur_' + color, color)
    inner = mat('ear_in', '#f4b7c0', 0.95)
    rot = Euler((0, 0, math.radians(lean)))
    ORG = Vector((x, 0.4, 0))
    def W(p): v = Vector(p); v.rotate(rot); return ORG + v
    inv = rot.to_matrix().inverted()
    # body + head + fluffy cheeks + feet in one seamless metaball
    bo = blob(name + '_b', [(W((0, 0, 0.52)), (0.6, 0.52, 0.5)), (W((0, -0.03, 1.26)), (0.58, 0.5, 0.5)),
                       (W((-0.3, -0.2, 1.14)), (0.2, 0.16, 0.14)), (W((0.3, -0.2, 1.14)), (0.2, 0.16, 0.14)),
                       (W((-0.27, -0.3, 0.06)), (0.17, 0.22, 0.08)), (W((0.27, -0.3, 0.06)), (0.17, 0.22, 0.08))], body)
    LV = [inv @ (bo.matrix_world @ v.co - ORG) for v in bo.data.vertices]
    def ext(z, band=0.03):
        sl = [v for v in LV if abs(v.z - z) < band and abs(v.x) < 0.75]
        return (max(abs(v.x) for v in sl), min(v.y for v in sl), max(v.y for v in sl))
    TOP = max(v.z for v in LV)
    def surf(x0, z0, r=0.05):
        return min(v.y for v in LV if abs(v.x - x0) < r and abs(v.z - z0) < r)
    print('TOP', TOP, flush=True)
    sphere(W((0, 0.5, 0.4)), (0.17, 0.17, 0.17), body, 24)          # tail
    # ears: long, slightly apart; droop on ouch
    for s in (-1, 1):
        if pose == 'ouch': tilt = (math.radians(-25), math.radians(s * 70), 0); base = (s * 0.3, 0.02, TOP - 0.12)
        elif pose == 'cheer': tilt = (0, math.radians(s * 22), 0); base = (s * 0.2, 0.02, TOP - 0.06)
        else: tilt = (math.radians(-6), math.radians(s * 12), 0); base = (s * 0.19, 0.02, TOP - 0.06)
        e_rot = Euler(tilt); e_rot.rotate(rot)
        off = Vector((0, 0, 0.34)); off.rotate(Euler(tilt))
        sphere(W(Vector(base) + off), (0.12, 0.08, 0.4), body, 32, e_rot)
        sphere(W(Vector(base) + off * 1.04 + Vector((0, -0.06, 0))), (0.065, 0.03, 0.28), inner, 24, e_rot)
    if os.environ.get('NOCOAT'): return list(set(bpy.data.objects) - before), []
    # happi coat: a copy of the body surface from chest to hips, open at the front, thickened outward
    coat_m = mat('coat_' + coat, coat, 0.9, 0.1)
    hp = bo.copy(); hp.data = bo.data.copy(); bpy.context.collection.objects.link(hp)
    hp.data.materials.clear(); hp.data.materials.append(coat_m)
    bm = bmesh.new(); bm.from_mesh(hp.data); M = hp.matrix_world
    def loc(v): return inv @ (M @ v.co - ORG)
    kill = [v for v in bm.verts if (lambda p: p.z > 0.86 or p.z < 0.2 or (p.y < 0 and abs(p.x) < 0.1 + (0.86 - p.z) * 0.12))(loc(v))]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(hp.data); bm.free()
    so = hp.modifiers.new('so', 'SOLIDIFY'); so.thickness = 0.05; so.offset = 1
    # white collar trim along the front opening + belt
    collar = mat('collar', '#fbf8f1', 0.9)
    for sx in (-1, 1):
        pts = []
        for i in range(9):
            z = 0.3 + i * 0.07; w, fy, _ = ext(z)
            xo = 0.1 + (0.86 - z) * 0.12
            # y of the surface at x=xo: approximate ellipse
            yy = fy * math.sqrt(max(0.05, 1 - (xo / w) ** 2))
            pts.append(W((sx * xo, yy - 0.04, z)))
        for p0, p1 in zip(pts, pts[1:]): capsule(p0, p1, 0.04, collar, 'trim')
    wb, fb, bb = ext(0.36)
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.06, location=(0, 0, 0))
    bt = bpy.context.object; bt.data.materials.append(mat('belt_' + belt, belt, 0.85)); bt.scale = (wb + 0.05, (bb - fb) / 2 + 0.05, 1)
    bt.location = W((0, (bb + fb) / 2, 0.36)); bt.rotation_euler = rot; smooth(bt)
    bt.modifiers.new('n', 'TRIANGULATE')
    # 豆絞り headband with a knot on the side
    hb = dots_mat('mameshibori', '#fbf8f1', '#2f4f8f', 30, 0.17)
    zh = 1.5; wh, fh, bh = ext(zh)
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.05, major_segments=64, location=(0, 0, 0))
    h = bpy.context.object; h.data.materials.append(hb); h.scale = (wh + 0.02, (bh - fh) / 2 + 0.02, 1)
    h.location = W((0, (bh + fh) / 2, zh)); h.rotation_euler = Euler((math.radians(-6), 0, math.radians(lean))); smooth(h)
    sphere(W((wh + 0.02, (bh + fh) / 2 - 0.05, zh)), (0.08, 0.07, 0.07), hb, 20)
    for k in (-1, 1):
        sphere(W((wh + 0.1, (bh + fh) / 2 - 0.05, zh - 0.05 + k * 0.05)), (0.13, 0.03, 0.05), hb, 16, Euler((0, math.radians(-35 * k - 20), math.radians(lean))))
    # face
    fz = 1.24
    face(lambda px, pz: W((px, surf(px, pz) + 0.005, pz)), 0, fz, 1.35, ouch=(pose == 'ouch'), happy=(pose == 'cheer'))
    sphere(W((0, surf(0, 1.16) - 0.005, 1.16)), (0.04, 0.02, 0.028), mat('nose', '#d9707e', 0.9), 16)
    brn = mat('mouth', '#4a2c1d', 1.0, 0.0)
    for k in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.009, depth=0.06, location=W((k * 0.022, surf(k * 0.022, 1.1) + 0.003, 1.1)), rotation=(0, math.radians(k * 50), 0))
        bpy.context.object.data.materials.append(brn)
    body_objs = list(set(bpy.data.objects) - before)
    # arms (separate list so 'hold' arms can be drawn over the mallet)
    before = set(bpy.data.objects)
    paw = fur('paw_' + color, color)
    pad = mat('pad', '#f4c4cb', 0.95)
    def arm(sh, hand):
        capsule(W(sh), hand if isinstance(hand, Vector) else W(hand), 0.13, paw)
        h = hand if isinstance(hand, Vector) else W(hand)
        sphere(h, (0.16, 0.15, 0.14), paw, 24)
        sphere(h + Vector((0, -0.1, 0)), (0.07, 0.03, 0.06), pad, 12)
    if pose == 'hold':
        arm((0.4, -0.2, 0.95), Vector(KPIV) + Vector((0, -0.12, 0)))
        arm((-0.38, -0.25, 0.8), (-0.08, -0.55, 0.62))
    elif pose == 'reach':
        arm((-0.4, -0.2, 0.9), Vector((0.4, 0.05, 1.42)))
        arm((0.38, -0.25, 0.8), (0.1, -0.55, 0.62))
    elif pose == 'cheer':
        arm((-0.42, -0.15, 0.95), (-0.72, -0.25, 1.75)); arm((0.42, -0.15, 0.95), (0.72, -0.25, 1.75))
    elif pose == 'ouch':
        arm((-0.4, -0.25, 0.9), (-0.25, -0.6, 1.0)); arm((0.4, -0.25, 0.9), (0.25, -0.6, 1.0))
    else:
        arm((-0.38, -0.25, 0.8), (-0.12, -0.55, 0.6)); arm((0.38, -0.25, 0.8), (0.12, -0.55, 0.6))
    return body_objs, list(set(bpy.data.objects) - before)

def build_kine():
    """Mallet lying along +X from the pivot (handle end) — the game rotates it around PIVOT."""
    m = wood('kine', '#9a6a44', '#b5845a')
    L = 1.27
    cyl((KPIV[0] + L / 2 - 0.1, KPIV[1], KPIV[2]), 0.06, L, m, 24, (0, math.radians(90), 0))
    h = cyl((KPIV[0] + L, KPIV[1], KPIV[2]), 0.25, 0.85, m, 48, (0, 0, 0))
    bevel(h, 0.05)
    for dz in (0.34, -0.34):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.025, location=(KPIV[0] + L, KPIV[1], KPIV[2] + dz))
        bpy.context.object.data.materials.append(mat('band', '#3a3330', 0.6))
    return L

def sky_world(sc):
    w = sc.world; nt = w.node_tree
    bg = nt.nodes['Background']; bg.inputs[1].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Window'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs[1], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (*srgb('#46598f'), 1); ramp.color_ramp.elements[1].color = (*srgb('#151b3a'), 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs[0])

MOON = (1.38, 10.0, 0.0, 0.78)    # x, y(depth), z (set below), radius
MOON_PY = 150
MOON = (MOON[0], MOON[1], zfor(MOON_PY, MOON[1]), MOON[3])

def build_moon():
    """Full moon: warm emissive disc with maria (the 'rabbit') + fine crater bump. Glow is drawn in-game."""
    sc = reset(); sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    m = bpy.data.materials.new('moon'); m.use_nodes = True; nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'BSDF_PRINCIPLED': nt.nodes.remove(nd)
    out = nt.nodes['Material Output']; em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 1.6; n1.inputs['Detail'].default_value = 3; n1.inputs['Roughness'].default_value = 0.55
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
    r1 = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(n1.outputs['Fac'], r1.inputs['Fac'])
    r1.color_ramp.elements[0].position = 0.5; r1.color_ramp.elements[1].position = 0.58
    r1.color_ramp.elements[0].color = (*srgb('#fff1c4'), 1); r1.color_ramp.elements[1].color = (*srgb('#e8cf8e'), 1)
    n2 = nt.nodes.new('ShaderNodeTexVoronoi'); n2.inputs['Scale'].default_value = 7
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    r2 = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(n2.outputs['Distance'], r2.inputs['Fac'])
    r2.color_ramp.elements[0].position = 0.08; r2.color_ramp.elements[1].position = 0.16
    r2.color_ramp.elements[0].color = (0.82, 0.8, 0.75, 1); r2.color_ramp.elements[1].color = (1, 1, 1, 1)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 0.5
    nt.links.new(r1.outputs['Color'], mul.inputs[6]); nt.links.new(r2.outputs['Color'], mul.inputs[7])
    # limb darkening: facing ratio
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    r3 = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(lw.outputs['Facing'], r3.inputs['Fac'])
    r3.color_ramp.elements[0].color = (1, 1, 1, 1); r3.color_ramp.elements[1].color = (0.82, 0.72, 0.55, 1)
    mul2 = nt.nodes.new('ShaderNodeMix'); mul2.data_type = 'RGBA'; mul2.blend_type = 'MULTIPLY'; mul2.inputs[0].default_value = 1
    nt.links.new(mul.outputs[2], mul2.inputs[6]); nt.links.new(r3.outputs['Color'], mul2.inputs[7])
    nt.links.new(mul2.outputs[2], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])
    e = math.radians(ELEV)
    o = sphere(MOON[:3], (MOON[3],) * 3, m, 96, (math.radians(90) - e, 0, 0.3))
    render(sc, 'moon')

def build_clouds():
    """Soft night clouds lit from behind by the moon; drawn in front of the moon and drifting in-game."""
    sc = reset(); sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    cm = mat('cloud', '#56649a', 1.0, 0.0, emit=('#3c4880', 0.4))
    cm.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = 1.0
    cm.node_tree.nodes['Principled BSDF'].inputs['Sheen Tint'].default_value = (*srgb('#fff0c8'), 1)
    bpy.ops.object.light_add(type='POINT', location=(MOON[0], MOON[1] + 2, MOON[2] + 0.2)); l = bpy.context.object; l.data.energy = 3000; l.data.color = srgb('#ffe9b8'); l.data.shadow_soft_size = 1.5
    random.seed(21)
    def puff(cx, cz, w, n):
        for i in range(n):
            u = (i / (n - 1) - 0.5) * 2
            r = (0.22 + 0.2 * (1 - u * u)) * w + random.uniform(-.03, .03)
            sphere((cx + u * w * 1.1, MOON[1] - 1.5, cz + r * 0.35 + (1 - u * u) * 0.08 * w), (r, r * 0.6, r * 0.75), cm, 24)
        for i in range(n + 2):   # flatter lower row so the cloud has a soft base instead of a slab
            u = (i / (n + 1) - 0.5) * 2
            r = 0.2 * w + random.uniform(0, .03)
            sphere((cx + u * w * 1.25, MOON[1] - 1.45, cz - 0.02), (r * 1.4, r * 0.5, r * 0.45), cm, 24)
    puff(MOON[0] - 0.55, MOON[2] - 0.62, 0.6, 7)
    puff(MOON[0] + 0.95, MOON[2] - 0.15, 0.36, 5)
    puff(-1.9, MOON[2] - 0.2, 0.5, 6)
    render(sc, 'clouds')

def build_bg():
    sc = reset(False); sky_world(sc)
    e = math.radians(ELEV)
    # distant hills
    hill = noise_mat('hillfar', '#26345c', '#2f4170', 2, 0.95, 0.2)
    for (hx, hr) in ((-3, 4), (3.2, 4.5)):
        sphere((hx, 12, -3.3), (hr, 0.5, 4.1), hill, 64)
    deck = wood('deck', '#6e4a36', '#7f5640')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4, -0.01)); p = bpy.context.object; p.scale = (12, 17, 1); p.data.materials.append(deck)
    field = noise_mat('field', '#22345a', '#2c4068', 3, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, -0.05)); p2 = bpy.context.object; p2.scale = (14, 8, 1); p2.data.materials.append(field)
    felt = noise_mat('felt', '#b8463e', '#c75249', 60, 0.95, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.4, 0.0)); f = bpy.context.object; f.scale = (5.2, 3.6, 0.04); f.data.materials.append(felt)
    bevel(f, 0.01, 2)
    stem = mat('susuki', '#b9a46a', 0.9); plume = noise_mat('plume', '#e7dcc0', '#f5eedc', 40, 0.95, 0.6)
    random.seed(3)
    for side in (-1, 1):
        for k in range(10):
            x = side * (2.3 + random.random() * 0.9); y = 1.8 + random.random() * 1.6
            h = 2.2 + random.random() * 1.8; lean = side * (0.08 + random.random() * 0.2)
            cyl((x + math.sin(lean) * h / 2, y, h / 2), 0.025, h, stem, 8, (0, lean, 0))
            sphere((x + math.sin(lean) * h, y, h + 0.1), (0.13, 0.13, 0.55), plume, 16, (0, lean + side * 0.4, 0))
    stand = wood('sanbo', '#d9b787', '#e8c99a')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.0, 2.4, 0.35)); s = bpy.context.object; s.scale = (0.8, 0.8, 0.7); s.data.materials.append(stand); bevel(s, 0.04)
    dango = mat('dango', '#fbf7ee', 0.85, sss=0.2)
    for lvl, n in enumerate((3, 2, 1)):
        for i in range(n):
            for j in range(n):
                sphere((-2.0 + (i - (n - 1) / 2) * 0.24, 2.4 + (j - (n - 1) / 2) * 0.24, 0.82 + lvl * 0.2), (0.13, 0.13, 0.12), dango, 24)
    paper = mat('andon', '#fff0d0', 0.9, emit=('#ffc777', 2.5))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.1, 2.6, 0.9)); a = bpy.context.object; a.scale = (0.5, 0.5, 1.1); a.data.materials.append(paper); bevel(a, 0.03)
    frame = mat('andonframe', '#3a2a22', 0.8)
    for dz in (0.35, 1.45):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(2.1, 2.6, dz)); fr = bpy.context.object; fr.scale = (0.56, 0.56, 0.06); fr.data.materials.append(frame)
    bpy.ops.object.light_add(type='POINT', location=(2.1, 2.2, 1.0)); l = bpy.context.object; l.data.energy = 120; l.data.color = srgb('#ffbb66')
    build_tray()
    st = mat('star', '#ffffff', 1.0, emit=('#fff6e0', 3.0))
    random.seed(9)
    for i in range(80):
        py = random.uniform(10, 420); px = random.uniform(20, 700)
        if math.hypot(px - (360 + MOON[0] * PXU), py - MOON_PY) < MOON[3] * PXU * 1.6: continue
        sphere(((px - 360) / PXU, 12, zfor(py, 12)), (0.018, 0.01, 0.018), st, 8)
    render(sc, 'bg')

TRAY = (0.0, -2.75, 0.0)
MARU = [(TRAY[0] + (c - 3.5) * 0.46, TRAY[1], 0.2) for c in range(8)]

def build_tray():
    """もろぶた: shallow wooden tray dusted with potato starch, where finished mochi balls get lined up"""
    w = wood('morobuta', '#b98a5e', '#c99a6c')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(TRAY[0], TRAY[1], 0.08)); b = bpy.context.object; b.scale = (3.7, 1.2, 0.16); b.data.materials.append(w); bevel(b, 0.03)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(TRAY[0], TRAY[1], 0.12)); cut = bpy.context.object; cut.scale = (3.5, 1.0, 0.2); cut.hide_render = True
    bo = b.modifiers.new('bool', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    flour = noise_mat('starch', '#efe9dc', '#fbf8f1', 25, 0.95, 0.4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(TRAY[0], TRAY[1], 0.05)); f = bpy.context.object; f.scale = (3.5, 1.0, 1); f.data.materials.append(flour)

def build_maru():
    m = mat('mochiS', '#fbf8f1', 0.32, 0.35, sss=0.45)
    x, y, z = MARU[0]
    sphere((x, y, z - 0.06), (0.24, 0.22, 0.14), m, 48)
    face(x, y - 0.21, z - 0.04, 0.55)

def only(fn, name):
    sc = reset(); fn(); render(sc, name)

def build_plate():
    sc = reset()
    stand = wood('sanbo', '#d9b787', '#e8c99a')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.3)); s = bpy.context.object; s.scale = (2.0, 1.4, 0.6); s.data.materials.append(stand); bevel(s, 0.05)
    m = mat('mochiF', '#fbf8f1', 0.4, 0.3, sss=0.45)
    sphere((0, 0.3, 1.05), (0.95, 0.85, 0.48), m, 64)
    sphere((0, 0.3, 1.72), (0.68, 0.6, 0.34), m, 64)
    mik = noise_mat('mikan', '#f08a2c', '#f6a24a', 30, 0.6, 0.5)
    sphere((0, 0.3, 2.22), (0.3, 0.3, 0.26), mik, 48)
    sphere((0.2, 0.3, 2.46), (0.16, 0.06, 0.03), mat('leaf', '#5f9a52', 0.8), 16, (0, math.radians(-20), 0))
    face(0, -0.57, 1.1, 1.6)
    render(sc, 'plate')

def rabbit_job(xr, color, lean, pose, name, coat, belt, arms_layer=False, hold_usu=False):
    sc = reset()
    if hold_usu: holdout(build_usu())
    b, a = rabbit(xr, color, lean, pose, name, coat, belt)
    if arms_layer:
        for o in a: o.hide_render = True
        render(sc, name)
        for o in a: o.hide_render = False
        for o in b: o.is_holdout = True
        render(sc, name + '_arm')
    else:
        render(sc, name)

A = (-1.82, '#fbf8f2', 14, '#2f4f8f', '#d9534a')
B = (1.84, '#e3c6a2', -14, '#c4473f', '#2f4f8f')
JOBS = {
    'bg': build_bg, 'moon': build_moon, 'clouds': build_clouds,
    'usu': lambda: only(build_usu, 'usu'),
    'mochi': lambda: [only(lambda s=s: build_mochi(s), 'mochi%d' % s) for s in range(3)],
    'usagi': lambda: rabbit_job(A[0], A[1], A[2], 'hold', 'usagi', A[3], A[4], arms_layer=True),
    'kine': lambda: only(build_kine, 'kine'),
    'turner': lambda: [rabbit_job(B[0], B[1], B[2], p, 'turner_' + p, B[3], B[4]) for p in os.environ.get('POSES', 'idle,reach,ouch,cheer').split(',')],
    'plate': build_plate,
    'maru': lambda: only(build_maru, 'maru'),
}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
meta = {'pivot': proj(*KPIV), 'mochi': proj(USU[0], USU[1], MOCHI_Z), 'mochiTop': proj(USU[0], USU[1] - 0.3, MOCHI_Z + 0.3),
        'maru': [proj(*p) for p in MARU], 'moon': proj(*MOON[:3]), 'moonR': MOON[3] * PXU, 'pxu': PXU, 'kineLen': 1.27}
json.dump(meta, open(os.path.join(OUT, 'scene.json'), 'w'))
