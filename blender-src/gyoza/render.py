# Renders the layers for gyoza.html (ぱりっと ぎょうざ): a kitchen counter seen from above (cutting board, filling bowl, wrapper stack, a tray)
# plus the wrapper / folded half-moon / finished and pan-fried gyoza sprites.
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


BOARD = (0.0, 0.2, 3.6, 3.0)
def build_bg():
    sc = reset(True)
    tile = noise_mat('tile', '#e8dcc4', '#ddd0b4', 3, 0.7, 0.05); box((0, 0, -0.6), (9, 12, 0.4), tile, 0.0)
    gm = mat('grout', '#d8ccb4', 0.9)
    for k in range(-6, 7): box((k * 0.8, 0, -0.39), (0.03, 12, 0.02), gm, 0.0); box((0, k * 0.8, -0.39), (9, 0.03, 0.02), gm, 0.0)
    bx, by, bw, bh = BOARD
    box((bx, by, -0.33), (bw, bh, 0.12), noise_mat('board', '#e0b88a', '#ecc89a', 3, 0.8, 0.1), 0.06)
    # filling bowl (top left), wrapper stack (top right), flour dust, the tray of finished gyoza at the bottom
    bowl = mat('bowl', '#f8f4ee', 0.35, 0.3); blue = mat('bowlb', '#4a7ab8', 0.5); fill = noise_mat('fill', '#d89a88', '#9ab868', 40, 0.9, 0.6, .45, .75, 3)
    cyl((-1.15, 2.85, -0.2), 0.68, 0.3, bowl, 64); cyl((-1.15, 2.85, -0.04), 0.58, 0.04, fill, 64)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.65, minor_radius=0.035, location=(-1.15, 2.85, -0.05)); o = bpy.context.object; o.data.materials.append(blue)
    skin = mat('skin', '#f2e4c4', 0.85, 0.1)
    for k in range(6): cyl((1.25 + k * 0.01, 2.85 - k * 0.01, -0.25 + k * 0.02), 0.52, 0.02, skin, 64)
    spoon = mat('spoon', '#c8c8cc', 0.3, 0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.04, depth=1.1, location=(-0.4, 3.3, -0.1), rotation=(0, math.radians(90), math.radians(-20))); o = bpy.context.object; o.data.materials.append(spoon)
    tray = mat('tray', '#3a3a40', 0.5, 0.3)
    box((0, -2.75, -0.32), (4.2, 1.5, 0.08), tray, 0.06)
    for (x, y, sx, sy) in ((0, -2.0, 4.3, 0.1), (0, -3.5, 4.3, 0.1), (-2.12, -2.75, 0.1, 1.6), (2.12, -2.75, 0.1, 1.6)): box((x, y, -0.27), (sx, sy, 0.14), tray, 0.03)
    render(sc, 'bg')
    META['board'] = [*tp(bx, by), bw * PXU, bh * PXU]; META['bowl'] = tp(-1.15, 2.85); META['stack'] = tp(1.25, 2.85); META['tray'] = [*tp(0, -2.75), 4.1 * PXU, 1.4 * PXU]

def half_moon(m, r=0.9, puff=0.28, pleats=0):
    """a folded gyoza seen from above: half disc puffed up, the curved edge at +y"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(0, 0, 0)); o = bpy.context.object
    o.scale = (r, r * 0.8, puff); smooth(o); o.data.materials.append(m)
    # flatten the back half into the straight fold
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -r * 0.5 - 0.0, 0)); c = bpy.context.object; c.scale = (3, r * 1.0, 2); c.hide_render = True
    bo = o.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'DIFFERENCE'
    # a thin flat rim along the curved edge
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r * 1.04, depth=0.03, location=(0, -0.0, -puff * 0.3)); rim = bpy.context.object; rim.scale = (1, 0.82, 1); rim.data.materials.append(m); smooth(rim)
    bo = rim.modifiers.new('b', 'BOOLEAN'); bo.object = c; bo.operation = 'DIFFERENCE'
    if pleats:
        dk = mat('pleat' + m.name, '#d8c8a8', 0.85, 0.1)
        for k in range(pleats):
            a = math.radians(30 + k * (120 / (pleats - 1)))
            x, y = math.cos(a) * r * 0.86, math.sin(a) * r * 0.84
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(x, y, puff * 0.25)); p = bpy.context.object
            p.scale = (0.05, 0.16, 0.06); p.rotation_euler = (0, 0, a - math.pi / 2); p.data.materials.append(dk); smooth(p)
    return o

def build_sprites():
    for name, kind in (('skin', 0), ('half', 1), ('gyoza', 2), ('yaki', 3)):
        sc = reset(True)
        skin = mat('skin', '#f2e4c4', 0.85, 0.1)
        if kind == 0:
            cyl((0, 0, 0), 0.9, 0.02, skin, 96)
            fill = noise_mat('fill', '#d89a88', '#9ab868', 40, 0.9, 0.6, .45, .75, 3)
        elif kind == 1: half_moon(skin, pleats=0)
        elif kind == 2: half_moon(skin, pleats=6)
        else:
            yk = noise_mat('yaki', '#d8a050', '#ecc88a', 5, 0.6, 0.3, .3, .7, 3)
            half_moon(yk, pleats=6)
        sprite_cam(sc, 2.2, 256); sc.render.resolution_x = sc.render.resolution_y = 256; render(sc, name)
    # a scoop of filling
    sc = reset(True); fill = noise_mat('fill', '#d89a88', '#9ab868', 40, 0.9, 0.6, .45, .75, 3)
    sphere((0, 0, 0), (0.4, 0.26, 0.16), fill, 48); sprite_cam(sc, 1.1, 128); sc.render.resolution_x = sc.render.resolution_y = 128; render(sc, 'filling')

JOBS = {'bg': build_bg, 'sprites': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
