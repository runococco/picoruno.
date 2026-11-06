# Renders the layers for kendama.html: the room (full frame, level camera) and the ken / tama sprites
# (side view, anchors recorded in scene.json).
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff0dc'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # warm afternoon light through the shoji from the left + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(55), math.radians(-35), math.radians(-30)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 600; a.data.size = 8; a.data.color = srgb('#ffe8d0')
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
CAT = (-1.45, 0.3)
def build_bg():
    sc = reset(False)
    tat = noise_mat('tatami', '#c8b878', '#d8c888', 60, 0.8, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -10, 0)); f = bpy.context.object; f.scale = (10, 24, 1); f.data.materials.append(tat)
    heri = mat('heri', '#3a4a3a', 0.7)
    for x in (-1.8, 1.8):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -10, 0.005)); h = bpy.context.object; h.scale = (0.08, 24, 0.01); h.data.materials.append(heri)
    # shoji wall with light coming through
    paper = mat('paper', '#fbf4e4', 0.9, 0.05, emit=('#fff2d8', 0.55)); fr = wood('shojifr', '#a8805a', '#8a643e')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.6, 2.7)); w = bpy.context.object; w.scale = (8, 0.04, 5.4); w.data.materials.append(paper)
    for k in range(-6, 7): bpy.ops.mesh.primitive_cube_add(size=1, location=(k * 0.7, 1.55, 2.7)); o = bpy.context.object; o.scale = (0.03, 0.04, 5.4); o.data.materials.append(fr)
    for k in range(0, 11): bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.535, 0.25 + k * 0.52)); o = bpy.context.object; o.scale = (8, 0.04, 0.03); o.data.materials.append(fr)
    for x in (-2.1, 0.0, 2.1):   # sliding door stiles
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 1.5, 2.7)); o = bpy.context.object; o.scale = (0.1, 0.08, 5.4); o.data.materials.append(fr)
    beam = wood('beam', '#7a5434', '#5a3c22')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.45, 5.45)); o = bpy.context.object; o.scale = (8, 0.16, 0.16); o.data.materials.append(beam)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.45, 0.05)); o = bpy.context.object; o.scale = (8, 0.16, 0.1); o.data.materials.append(beam)
    plaster = noise_mat('plaster', '#e8d8b8', '#f0e2c4', 8, 0.95, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.62, 7.0)); o = bpy.context.object; o.scale = (8, 0.04, 3.0); o.data.materials.append(plaster)
    # zabuton + sitting cat (eyes are drawn by the game so they can follow the ball)
    zb = noise_mat('zabuton', '#c8503a', '#d8604a', 20, 0.9, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(CAT[0], CAT[1], 0.06)); z = bpy.context.object; z.scale = (0.9, 0.8, 0.1); z.data.materials.append(zb); bevel(z, 0.04, 6)
    wh = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); og = mat('cato', '#e8a050', 0.85, 0.1); pk = mat('catpk', '#f4a8a0', 0.8)
    cx, cy = CAT
    sphere((cx, cy, 0.42), (0.3, 0.26, 0.32), wh, 48)
    sphere((cx + 0.12, cy - 0.04, 0.55), (0.14, 0.12, 0.12), og, 24)
    sphere((cx, cy - 0.05, 0.86), (0.25, 0.22, 0.21), wh, 48)
    sphere((cx - 0.1, cy - 0.08, 0.98), (0.12, 0.1, 0.08), og, 24)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.09, depth=0.16, location=(cx + s_ * 0.14, cy - 0.02, 1.08))
        e = bpy.context.object; e.rotation_euler = (0, s_ * 0.3, 0); e.data.materials.append(og if s_ < 0 else wh); smooth(e)
        sphere((cx + s_ * 0.16, cy - 0.24, 0.8), (0.05, 0.02, 0.03), pk, 12)
        sphere((cx + s_ * 0.12, cy - 0.22, 0.2), (0.07, 0.08, 0.06), wh, 16)          # front paws
    sphere((cx, cy - 0.27, 0.83), (0.025, 0.015, 0.018), pk, 12)                      # nose
    tail = [(cx + 0.28, cy, 0.12), (cx + 0.42, cy - 0.15, 0.1), (cx + 0.35, cy - 0.32, 0.1)]
    cu = bpy.data.curves.new('tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.05; sp = cu.splines.new('NURBS'); sp.points.add(2); sp.use_endpoint_u = True
    for j, p in enumerate(tail): sp.points[j].co = (*p, 1)
    ob = bpy.data.objects.new('tail', cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(og)
    META['catEyes'] = [[round(v, 1) for v in proj(cx + s_ * 0.09, cy - 0.25, 0.9)] for s_ in (-1, 1)]
    # low table with a basket of mikan
    tb = wood('table', '#8a5a34', '#6a4426')
    cyl((1.55, 0.2, 0.42), 0.75, 0.06, tb, 64)
    for a in (0.6, 2.2, 3.8, 5.4): cyl((1.55 + math.cos(a) * 0.5, 0.2 + math.sin(a) * 0.5, 0.2), 0.05, 0.4, tb, 12)
    bk = noise_mat('basket', '#b8905a', '#d0a870', 40, 0.8, 0.5)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.32, depth=0.14, location=(1.55, 0.2, 0.52)); b = bpy.context.object; b.scale = (1, 1, 1); b.data.materials.append(bk); smooth(b)
    mk = noise_mat('mikan', '#f08a1e', '#f8a032', 40, 0.5, 0.4)
    for (dx, dy, dz) in ((-0.12, 0, 0.66), (0.12, 0.03, 0.66), (0, -0.1, 0.66), (0.0, 0.08, 0.8)):
        sphere((1.55 + dx, 0.2 + dy, dz), (0.12, 0.12, 0.1), mk, 32)
    render(sc, 'bg')

SPR = {}
def side_cam(sc, scale, res, tz):
    for o in list(sc.objects):
        if o.type == 'CAMERA': bpy.data.objects.remove(o)
    loc = Vector((0, -30, tz)); bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (math.radians(90), 0, 0)
    c.data.type = 'ORTHO'; c.data.ortho_scale = scale; c.data.clip_end = 100; sc.camera = c
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + x * res / scale, 1), round(res / 2 - (z - tz) * res / scale, 1)]

def bowl(x, z, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(x, 0, z)); b = bpy.context.object; b.scale = (r, r, r * 0.55); smooth(b)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in b.data.vertices: v.select = v.co.z > 0.0
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
    sd = b.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.03; b.data.materials.append(m); return b

def build_ken():
    sc = reset(True)
    wd = wood('ken', '#e8c890', '#d0a868')
    cyl((0, 0, 0.42), 0.085, 0.84, wd, 32)                                  # handle
    sphere((0, 0, 0.0), (0.095, 0.095, 0.05), wd, 32)
    cyl((0, 0, 0.84), 0.075, 0.86, wd, 32, (0, math.radians(90), 0))       # cross piece
    for (x, r) in ((-0.43, 0.2), (0.43, 0.16)):
        cyl((x, 0, 0.9), 0.06, 0.14, wd, 24)                               # cup stems
        bowl(x, 1.0 + r * 0.55, r, wd)                                     # cups open upward
    cyl((0, 0, 0.98), 0.06, 0.3, wd, 32)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.06, radius2=0.012, depth=0.26, location=(0, 0, 1.26)); s = bpy.context.object; s.data.materials.append(wd); smooth(s)
    to2d = side_cam(sc, 1.6, 400, 0.66)
    SPR['ken'] = {'res': 400, 'pxu': 400 / 1.6, 'grip': to2d(0, 0.3), 'attach': to2d(0, 0.78), 'big': to2d(-0.43, 1.0 + 0.2 * 0.55 - 0.08), 'small': to2d(0.43, 1.0 + 0.16 * 0.55 - 0.06),
                  'bigR': 0.2, 'smallR': 0.16, 'spike': to2d(0, 1.39)}
    render(sc, 'ken')

def build_tama():
    sc = reset(True)
    rd = mat('tama', '#d8302a', 0.18, 0.7); wh = mat('stripe', '#fbf6ee', 0.25, 0.6); dk = mat('hole', '#2a0c08', 0.6)
    b = sphere((0, 0, 0), (0.14, 0.14, 0.14), rd, 64)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.035, depth=0.4, location=(0, 0, -0.14)); h = bpy.context.object; h.hide_render = True
    bo = b.modifiers.new('h', 'BOOLEAN'); bo.object = h; bo.operation = 'DIFFERENCE'
    bpy.ops.mesh.primitive_torus_add(major_radius=0.139, minor_radius=0.007, location=(0, 0, 0)); t = bpy.context.object; t.rotation_euler = (0, math.radians(90), 0); t.data.materials.append(wh)
    sphere((0, 0, -0.06), (0.03, 0.03, 0.05), dk, 16)
    for o in (b, t): o.rotation_euler.x += math.radians(-28)    # tilt the hole a little toward the camera so it reads
    side_cam(sc, 0.4, 120, 0.0)
    SPR['tama'] = {'res': 120, 'pxu': 120 / 0.4, 'r': 0.14}
    render(sc, 'tama')

JOBS = {'bg': build_bg, 'ken': build_ken, 'tama': build_tama}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
