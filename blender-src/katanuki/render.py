# Renders the layers for katanuki.html: a festival stall table seen from straight above
# (full frame) and the candy-plate / needle sprites (same top-down camera).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 89.9; TZ = 0.0     # straight down: frame row = 640 - y * 160
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#e8f4ff'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # bright summer sun from the upper left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.0; s.data.angle = math.radians(12); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(22), math.radians(-24), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 250; a.data.size = 8; a.data.color = srgb('#e8f0ff')
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
    sc.render.resolution_x = sc.render.resolution_y = res; bpy.context.view_layer.update()
    return lambda x, z: [round(res / 2 + x * res / scale, 1), round(res / 2 - (z - tz) * math.cos(e) * res / scale, 1)]

TABLE = (3.7, 6.1)        # table top size (x, y)

def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#fff0e0'), 1)
    # red felt over a wooden stall table
    felt = noise_mat('felt', '#c8322a', '#d8463a', 60, 0.95, 0.25)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); f = bpy.context.object; f.scale = (14, 14, 1); f.data.materials.append(felt)
    tray = wood('tray', '#b07a48', '#c8925a')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.05, 0.03)); o = bpy.context.object; o.scale = (4.3, 4.0, 0.06); o.data.materials.append(tray); bevel(o, 0.05)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.05, 0.04)); o = bpy.context.object; o.scale = (4.0, 3.7, 0.06); o.data.materials.append(mat('paper', '#f8f2e4', 0.9)); bevel(o, 0.02)
    random.seed(11)
    # spare candy plates stacked at the top, broken bits, coins, a ramune bottle lying down and a little tin of pins
    cols = ('#f0a0b4', '#98d8b4', '#f4d470', '#a8bcec')
    for k, (x, y) in enumerate(((-1.6, 3.2), (-0.55, 3.25), (0.5, 3.2), (1.55, 3.25))):
        for h in range(3):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x + random.uniform(-.03, .03), y + random.uniform(-.03, .03), 0.03 + h * 0.05)); o = bpy.context.object
            o.scale = (0.95, 0.8, 0.045); o.rotation_euler = (0, 0, random.uniform(-.08, .08)); o.data.materials.append(noise_mat('pl%d' % k, cols[k], '#fff4f0', 30, 0.8, 0.2, lo=.35, hi=.9)); bevel(o, 0.06, 3)
    for k in range(9):
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=random.uniform(.08, .15), depth=0.04, location=(random.choice((-1, 1)) * random.uniform(2.05, 2.25), random.uniform(-3.6, 2.4), 0.03)); o = bpy.context.object
        o.rotation_euler = (0, 0, random.uniform(0, 6)); o.data.materials.append(noise_mat('pl%d' % (k % 4), cols[k % 4], '#fff4f0', 30, 0.8, 0.2, lo=.35, hi=.9))
    coin = mat('coin', '#d8a850', 0.3, 0.8)
    for k in range(5): cyl((-2.0 + random.uniform(-.03, .03), -3.55, 0.03 + k * 0.025), 0.17, 0.02, coin, 32)
    cyl((-1.6, -3.75, 0.03), 0.17, 0.02, mat('coin2', '#c8c4c0', 0.3, 0.8), 32)
    glass = mat('ramune', '#7ac8e0', 0.08, 0.6); glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.6
    cyl((1.75, -3.55, 0.15), 0.14, 0.9, glass, 32, rot=(0, math.radians(90), 0.35))
    sphere((1.35, -3.7, 0.15), (0.06, 0.06, 0.06), mat('marble', '#c8e8f4', 0.05, 0.8), 16)
    render(sc, 'bg')
    META['plate'] = proj(0, 0, 0.08)

def build_sprites():
    for name, col, col2 in (('plate_pink', '#f0a0b4', '#f8c4d0'), ('plate_mint', '#98d8b4', '#bce8cc'), ('plate_lemon', '#f4d470', '#f8e49c')):
        sc = reset(True)   # a powdery pressed-candy plate
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (3.6, 3.3, 0.08)
        o.data.materials.append(noise_mat('pl' + name, col, col2, 90, 0.85, 0.25, lo=.3, hi=.8)); bevel(o, 0.22, 5)
        sprite_cam(sc, 4.0, 640); SPR['plate'] = {'res': 640, 'pxu': 160.0, 'w': 3.6 * 160, 'h': 3.3 * 160}
        render(sc, name)
    sc = reset(True)   # a sewing pin with a red bead, lying along y with the tip at -y
    cyl((0, 0, 0.03), 0.012, 1.1, mat('steel', '#c8ccd2', 0.2, 0.9), 16, rot=(math.radians(90), 0, 0))
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.012, depth=0.06, location=(0, -0.58, 0.03), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.data.materials.append(mat('steel', '#c8ccd2', 0.2, 0.9)); smooth(o)
    sphere((0, 0.58, 0.06), (0.07, 0.07, 0.07), mat('bead', '#d8322a', 0.25, 0.5), 32)
    sprite_cam(sc, 1.4, 224); SPR['pin'] = {'res': 224, 'pxu': 160.0, 'tip': [112.0, round(112 + 0.61 * 160, 1)]}
    render(sc, 'pin')

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
