# Renders the layers for origami.html from straight above: a desk with a green cutting mat (background) and five washi
# paper tiles (four printed chiyogami patterns + plain white back) with paper-fibre bump, used as canvas fill patterns.
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




from PIL import Image, ImageDraw

def pil_pattern(kind, N=512):
    im = Image.new('RGB', (N, N)); d = ImageDraw.Draw(im)
    if kind == 'ichimatsu':
        k = N // 4
        for i in range(4):
            for j in range(4): d.rectangle([i * k, j * k, (i + 1) * k, (j + 1) * k], fill='#d84a4a' if (i + j) % 2 else '#f6e6cc')
    elif kind == 'seigaiha':
        d.rectangle([0, 0, N, N], fill='#2e6eb0'); R = N // 4; circ = []
        for row in range(8):
            for col in range(3):
                cx = col * 2 * R + (R if row % 2 else 0); cy = row * R // 2
                for ox in (-N, 0, N):
                    for oy in (-N, 0, N): circ.append((cy + oy, cx + ox))
        for cy, cx in sorted(circ):
            for k, c in enumerate(['#f4f0e4', '#2e6eb0', '#f4f0e4', '#2e6eb0', '#f4f0e4', '#2e6eb0']):
                r = R - k * R // 6; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    elif kind == 'sakura':
        d.rectangle([0, 0, N, N], fill='#f2a0b8')
        for (fx, fy, s) in [(110, 120, 60), (360, 90, 44), (250, 300, 70), (440, 380, 54), (90, 420, 46), (400, 230, 30), (180, 250, 26)]:
            for ox in (-N, 0, N):
                for oy in (-N, 0, N):
                    for k in range(5):
                        a = k * 2 * math.pi / 5 - math.pi / 2; px, py = fx + ox + math.cos(a) * s * .55, fy + oy + math.sin(a) * s * .55
                        d.ellipse([px - s * .42, py - s * .42, px + s * .42, py + s * .42], fill='#fff4f6')
                    d.ellipse([fx + ox - s * .18, fy + oy - s * .18, fx + ox + s * .18, fy + oy + s * .18], fill='#e8708e')
    elif kind == 'shima':
        k = N // 8
        for i in range(8): d.rectangle([i * k, 0, (i + 1) * k, N], fill=['#f2c43a', '#e8903a'][i % 2])
        for i in range(8): d.rectangle([i * k + k // 2 - 3, 0, i * k + k // 2 + 3, N], fill='#fff4d8')
    elif kind == 'back':
        d.rectangle([0, 0, N, N], fill='#f6f0e2')
    return im

def build_paper(kind):
    sc = reset(False); top_cam(sc, 1.0, 512)
    p = os.path.join(OUT, f'_src_{kind}.png'); pil_pattern(kind).save(p)
    m = bpy.data.materials.new('pp' + kind); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(p); tx.interpolation = 'Closest'
    nt.links.new(tx.outputs['Color'], b.inputs['Base Color'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 6, 1); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.9; b.inputs['Specular IOR Level'].default_value = 0.05
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.data.materials.append(m)
    # world light only, flat and even so the tile stays seamless
    for ob in list(sc.objects):
        if ob.type == 'LIGHT': bpy.data.objects.remove(ob)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1); sc.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); s = bpy.context.object; s.data.energy = 0.6; s.rotation_euler = (math.radians(35), 0, math.radians(30))
    render(sc, 'pp_' + kind); os.remove(p)

def build_bg():
    sc = reset(False)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.1)); o = bpy.context.object; o.scale = (6, 10, 1)
    tm = bpy.data.materials.new('tatami'); tm.use_nodes = True; nt = tm.node_tree; b = nt.nodes['Principled BSDF']
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 0.6; wv.inputs['Detail'].default_value = 2
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#b8b070'), 1); r.color_ramp.elements[1].color = (*srgb('#cfc68a'), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.3; nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.85; o.data.materials.append(tm)
    for sy in (-1, 1): box((0, sy * 3.2, -0.08), (6, 0.25, 0.03), mat('heri', '#3a4a6a', 0.8), 0.01)
    # a green felt desk mat with a faint grid, and a little paper tray for finished pieces
    felt = noise_mat('felt', '#5e8a5a', '#6a9666', 40, 0.95, 0.15)
    box((0, 0, -0.05), (3.9, 4.6, 0.04), felt, 0.03)
    gl = mat('grid', '#7aa676', 0.95)
    for i in range(-6, 7):
        box((i * 0.3, 0, -0.025), (0.008, 4.4, 0.004), gl, 0.001)
    for j in range(-7, 8):
        box((0, j * 0.3, -0.025), (3.7, 0.008, 0.004), gl, 0.001)
    tx, ty = 0, (640 - 1170) / PXU
    box((tx, ty, -0.05), (3.9, 0.7, 0.1), wood('tray', '#c89a62', '#b88a52'), 0.04)
    box((tx, ty, 0.0), (3.7, 0.5, 0.04), mat('trayin', '#f4ecdc', 0.85), 0.01)
    render(sc, 'bg')

JOBS = {'bg': build_bg}
for k in ['ichimatsu', 'seigaiha', 'sakura', 'shima', 'back']: JOBS[k] = (lambda k=k: build_paper(k))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
