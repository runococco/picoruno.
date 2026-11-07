# Renders the layers for sentaku.html: a sunny backyard with two laundry poles (side view, sky transparent)
# and the laundry pieces as flat cloth sprites hanging from their top edge.
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 5.0; TZ = 0.0      # almost level: frame row ~ 640 - z * 160
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
    # warm afternoon light from above-left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 8; a.data.color = srgb('#e0ecff')
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

GROUND = -2.9; LINE_Z = 2.2; POLE_X = 2.05
def build_bg():
    sc = reset(True)
    grass = noise_mat('grass', '#86c060', '#9ad070', 6, 0.9, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, GROUND)); o = bpy.context.object; o.scale = (16, 40, 1); o.data.materials.append(grass); o.visible_diffuse = False
    # wooden fence, a hedge and a far hill line
    fw = wood('fence', '#c8a070', '#d6b080')
    for k in range(-9, 10):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(k * 0.44, 4.5, GROUND + 0.75)); o = bpy.context.object; o.scale = (0.32, 0.06, 1.5); bevel(o, 0.03); o.data.materials.append(fw)
    for z in (0.35, 1.15):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.42, GROUND + z)); o = bpy.context.object; o.scale = (9, 0.05, 0.12); o.data.materials.append(fw)
    hill = noise_mat('hill', '#8ac070', '#9ccc80', 3, 0.95, 0.2); tree = noise_mat('tree', '#5aa050', '#6ab45a', 5, 0.95, 0.5)
    for k in range(4): sphere((-5 + k * 3.4, 30, GROUND - 1.5), (3.4, 2, 2.6), hill, 48)
    for (x, r) in ((-2.6, 1.0), (2.8, 1.2), (0.6, 0.8)): sphere((x, 6, GROUND + 1.6), (r, r * 0.8, r), tree, 48)
    # the two poles and the cross bars the line hangs between
    pole = wood('pole', '#8a6040', '#a07450')
    for s in (-1, 1):
        cyl((s * POLE_X, 0.3, (GROUND + LINE_Z + 0.4) / 2), 0.07, LINE_Z + 0.4 - GROUND, pole, 24)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(s * POLE_X, 0.3, LINE_Z)); o = bpy.context.object; o.scale = (0.12, 0.6, 0.1); o.data.materials.append(pole)
        cyl((s * POLE_X, 0.3, GROUND + 0.06), 0.24, 0.12, mat('stone', '#a8a49c', 0.9), 32)
    # a basket by the left pole and the cat sitting next to it
    bk = noise_mat('basket', '#c89858', '#d8a868', 40, 0.9, 0.6, .3, .7, 2)
    cyl((-1.2, -0.6, GROUND + 0.22), 0.45, 0.44, bk, 48)
    cw = mat('fur', '#fbf6ec', 0.85, 0.1); cp = mat('patch', '#e8a050', 0.85, 0.1); cp2 = mat('patch2', '#4a4248', 0.85, 0.1); blk = mat('eye', '#1a1210', 0.9, 0.0); pink = mat('nose', '#e88a8a', 0.8)
    X, Y = 0.95, -0.8; B = (X, Y, GROUND + 0.34); bs = (0.32, 0.27, 0.36); sphere(B, bs, cw, 64)
    paint_on(B, bs, cp, (X + 0.3, Y - 0.1, B[2] + 0.2), (0.25, 0.4, 0.3))
    hl = (X, Y - 0.02, GROUND + 0.86); hs = (0.3, 0.26, 0.26); sphere(hl, hs, cw, 64)
    paint_on(hl, hs, cp2, (X - 0.26, Y - 0.1, hl[2] + 0.2), (0.25, 0.4, 0.24))
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.1, depth=0.2, location=(X + s_ * 0.18, Y, hl[2] + 0.25)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.4, 0); e.data.materials.append(cp2 if s_ < 0 else cw); smooth(e)
        sphere((X + s_ * 0.1, Y - 0.24, hl[2] + 0.04), (0.04, 0.02, 0.05), blk, 24)
        sphere((X + s_ * 0.15, Y - 0.2, GROUND + 0.05), (0.08, 0.1, 0.06), cw, 24)
    sphere((X, Y - 0.26, hl[2] - 0.05), (0.026, 0.02, 0.02), pink, 16)
    render(sc, 'bg')
    META['line'] = [proj(-POLE_X, 0.3, LINE_Z), proj(POLE_X, 0.3, LINE_Z)]; META['ground'] = proj(0, 0, GROUND)[1]

def cloth(name, pts, color, stripe=None, w=1.0):
    """flat cloth cut from a 2D outline (x right, z down from the top edge, in units), rendered face-on"""
    sc = reset(True)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x, 0, -z)) for x, z in pts]; f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:]); bmesh.ops.translate(bm, vec=(0, 0.03, 0), verts=[v for v in r['geom'] if isinstance(v, bmesh.types.BMVert)])
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    bevel(o, 0.012, 2); o.data.materials.append(noise_mat('c' + name, color, color, 3, 0.95, 0.5, .3, .7, 2))
    if stripe:
        for (z0, z1, c) in stripe:
            bpy.ops.mesh.primitive_cube_add(size=1, location=(w / 2, -0.03, -(z0 + z1) / 2)); s = bpy.context.object; s.scale = (w * 0.98, 0.01, z1 - z0); s.data.materials.append(mat('s' + name + c, c, 0.95, 0.1))
    side_cam(sc, 2.0, 256, -0.9, 0.0)
    for ob in bpy.context.scene.objects:
        if ob.type == 'MESH': ob.location.x -= w / 2
    render(sc, name)

ITEMS = {
  'towel': ([(0, 0), (1.5, 0), (1.5, 1.3), (0, 1.3)], '#f2a0a8', [(0.95, 1.05, '#fbf6ec'), (1.1, 1.15, '#fbf6ec')], 1.5),
  'hand': ([(0, 0), (0.95, 0), (0.95, 0.9), (0, 0.9)], '#8cc8e8', [(0.7, 0.78, '#fbf6ec')], 0.95),
  'sock': ([(0, 0), (0.42, 0), (0.42, 0.75), (0.62, 0.85), (0.6, 1.08), (0.1, 1.08), (0, 0.95)], '#f4c430', [(0.0, 0.1, '#fbf6ec')], 0.62),
  'shirt': ([(0.3, 0), (0.5, 0.1), (0.8, 0.1), (1.0, 0), (1.3, 0.22), (1.18, 0.48), (1.02, 0.4), (1.02, 1.25), (0.28, 1.25), (0.28, 0.4), (0.12, 0.48), (0, 0.22)], '#9ad070', None, 1.3),
  'hanky': ([(0, 0), (0.68, 0), (0.68, 0.68), (0, 0.68)], '#c8a8e0', [(0.08, 0.12, '#fbf6ec'), (0.56, 0.6, '#fbf6ec')], 0.68),
  'shorts': ([(0, 0), (1.1, 0), (1.15, 0.95), (0.66, 0.98), (0.55, 0.45), (0.44, 0.98), (-0.05, 0.95)], '#5a8ad0', [(0.0, 0.1, '#fbf6ec')], 1.1),
  'pillow': ([(0, 0), (1.2, 0), (1.2, 0.8), (0, 0.8)], '#fbf6ec', [(0.3, 0.38, '#f2a0a8'), (0.45, 0.53, '#f2a0a8')], 1.2),
}
def build_items():
    for k, (pts, c, st, w) in ITEMS.items(): cloth(k, pts, c, st, w)
    META['items'] = {k: v[3] for k, v in ITEMS.items()}

JOBS = {'bg': build_bg, 'items': build_items}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
