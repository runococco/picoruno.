# Renders the layers for uchimizu.html from straight above: a summer garden path of 5x7 flagstones between bamboo fences,
# a straw nest (goal), the chick basket (start) and a wooden water bucket, plus chicks (yellow / gold, two walk poses).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 89.9; TZ = 0.0      # straight down: frame row ~ 640 - y * 160
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe6ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # warm kitchen light from above-left + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.7; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(-2, -3, 8))
    a = bpy.context.object; a.data.energy = 260; a.data.size = 8; a.data.color = srgb('#e0ecff')
    a.rotation_euler = (Vector((0, 0, 3)) - a.location).to_track_quat('-Z', 'Y').to_euler()
    e = math.radians(ELEV); d = 40
    loc = Vector((0, 0, 40))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (0, 0, 0)
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
def side_cam(sc, scale, res, tz, tx=0.0):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    loc = Vector((tx, -30, tz)); bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + (x - tx) * res / scale, 1), round(res / 2 - (z - tz) * res / scale, 1)]

def disc(loc, r, m, depth=0.01, verts=48):
    """flat painted disc facing the camera (-y)"""
    return cyl(loc, r, depth, m, verts, rot=(math.radians(90), 0, 0))

def paint_on(base_loc, base_scale, m, cutter_loc, cutter_scale, seg=48, rot=(0, 0, 0)):
    o = sphere(base_loc, tuple(v * 1.012 for v in base_scale), m, seg, rot)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=cutter_loc); c = bpy.context.object; c.scale = cutter_scale; c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'INTERSECT'; return o
def box(loc, sc_, m, bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = sc_; o.data.materials.append(m); bevel(o, bev, 3); return o
def tp(x, y): return [round(RES[0] / 2 + x * PXU, 1), round(RES[1] / 2 - y * PXU, 1)]

def top_cam(sc, scale, res):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    bpy.ops.object.camera_add(location=(0, 0, 30)); c = bpy.context.object; c.rotation_euler = (0, 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res

def planks():
    m = bpy.data.materials.new('planks'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (6, 0.6, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 5; wv.inputs['Detail'].default_value = 4; wv.inputs['Detail Scale'].default_value = 1.5
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#b07a48'), 1); r.color_ramp.elements[1].color = (*srgb('#c28c58'), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.75; b.inputs['Specular IOR Level'].default_value = .12
    return m




GX0, GY0, T, NC, NR = 80, 280, 112, 5, 7      # stone grid in frame px

def W(px, py): return ((px - 360) / PXU, (640 - py) / PXU)

def build_bg():
    sc = reset(False)
    gravel = noise_mat('gravel', '#d8d0c0', '#c4baa6', 90, 0.95, 0.6, .25, .75)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.1)); o = bpy.context.object; o.scale = (6, 10, 1); o.data.materials.append(gravel)
    moss = noise_mat('moss', '#6a8a48', '#82a05a', 20, 0.95, 0.4)
    x0, y0 = W(GX0, GY0); x1, y1 = W(GX0 + NC * T, GY0 + NR * T)
    box(((x0 + x1) / 2, (y0 + y1) / 2, -0.09), (x1 - x0 + 0.1, y0 - y1 + 0.1, 0.02), moss, 0.02)
    rnd = random.Random(5)
    stones = [noise_mat('st%d' % i, c1, c2, 9, 0.85, 0.35) for i, (c1, c2) in enumerate([('#a8a49a', '#bcb8ae'), ('#9ea2a0', '#b2b6b2'), ('#b0a898', '#c2baaa')])]
    t = T / PXU
    for r in range(NR):
        for c in range(NC):
            cx, cy = W(GX0 + (c + .5) * T, GY0 + (r + .5) * T)
            o = box((cx + rnd.uniform(-.01, .01), cy + rnd.uniform(-.01, .01), -0.05), (t - .07, t - .07, 0.1), stones[rnd.randrange(3)], 0.05)
            o.rotation_euler = (0, 0, rnd.uniform(-.04, .04))
    # bamboo fences on both sides
    bam = noise_mat('bamboo', '#c8b070', '#b8a060', 30, 0.6, 0.2)
    for sx in (-1, 1):
        x = sx * 2.05
        for k in range(14):
            cyl((x + sx * (k % 2) * 0.06, -4.6 + k * 0.7, 0.0), 0.06, 0.66, bam, 16, rot=(math.radians(90), 0, 0))
        for yy in (-2.4, 0.0, 2.4): cyl((x, yy, 0.08), 0.035, 0.5, mat('rope', '#6a4a2a', 0.9), 12, rot=(0, math.radians(90), 0))
    # straw nest at the top, chick basket at the bottom
    straw = noise_mat('straw', '#e0c070', '#c8a050', 40, 0.9, 0.6)
    nx, ny = W(360, 205)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.16, location=(nx, ny, 0.0)); o = bpy.context.object; o.scale = (1.25, 0.8, 0.8); smooth(o); o.data.materials.append(straw)
    cyl((nx, ny, -0.05), 0.42, 0.04, mat('nestin', '#b89048', 0.9), 48).scale = (1.25, 0.8, 1)
    bx, by = W(360, 1135)
    box((bx, by, -0.02), (1.3, 0.55, 0.16), wood('basket', '#c89a62', '#b88a52'), 0.06)
    box((bx, by, 0.06), (1.16, 0.42, 0.04), mat('basketin', '#8a6a3a', 0.9), 0.01)
    # wooden bucket with water and a ladle, bottom left
    kx, ky = W(95, 1180)
    cyl((kx, ky, 0.0), 0.36, 0.3, wood('oke', '#c8a070', '#b08858'), 48)
    for zz in (-0.08, 0.08):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.365, minor_radius=0.018, location=(kx, ky, 0.0)); o = bpy.context.object; o.location.z = zz + 0.0; smooth(o); o.data.materials.append(mat('hoop', '#5a4a3a', 0.6, 0.3))
    wm = bpy.data.materials.new('wat'); wm.use_nodes = True; b = wm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*srgb('#5ab0d8'), 1); b.inputs['Roughness'].default_value = 0.15
    cyl((kx, ky, 0.155), 0.32, 0.01, wm, 48)
    cyl((kx + 0.12, ky + 0.05, 0.19), 0.11, 0.06, wood('hish', '#d8b080', '#c09868'), 32)
    box((kx + 0.45, ky + 0.25, 0.2), (0.6, 0.04, 0.03), wood('hand', '#d8b080', '#c09868'), 0.01).rotation_euler = (0, 0, math.radians(35))
    render(sc, 'bg')

def eyes(x, y, z, dx, r=0.03):
    blk = mat('blk', '#1e1410', 0.6, 0.05)
    for s in (-1, 1): sphere((x + s * dx, y, z), (r, r, r * .6), blk, 16)

def build_chick(name, col, step):
    sc = reset(True); top_cam(sc, 0.8, 128)
    y_ = mat('hy' + name, col, 0.7, 0.1); org = mat('beak', '#f08a2a', 0.6)
    sphere((0, -0.02, 0.15), (0.2, 0.22, 0.17), y_, 48)
    sphere((0, 0.13, 0.27), (0.13, 0.12, 0.11), y_, 40)
    for s in (-1, 1): sphere((s * 0.18, -0.04, 0.16), (0.06, 0.12, 0.05), y_, 24, rot=(0, 0, s * (-0.3 - 0.15 * step)))
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.04, depth=0.09, location=(0, 0.27, 0.27)); o = bpy.context.object; o.rotation_euler = (math.radians(-90), 0, 0); o.data.materials.append(org)
    eyes(0, 0.19, 0.36, 0.055)
    for s in (-1, 1): sphere((s * 0.08, 0.15 + (0.05 if (s > 0) == bool(step) else -0.02), 0.03), (0.04, 0.07, 0.02), org, 16)
    render(sc, f'{name}{step}')

JOBS = {'bg': build_bg}
for nm, col in (('hy', '#ffd84a'), ('gold', '#f2b42a')):
    for st in (0, 1): JOBS[f'{nm}{st}'] = (lambda nm=nm, col=col, st=st: build_chick(nm, col, st))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
