# Renders the layers for suikawari.html: a summer beach seen from a raised camera (full frame) and the
# watermelon / cracked watermelon / stick / cat sprites (same raised ortho camera).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 58.0; TZ = 0.0     # raised: ground rows squeeze by sin(58)
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
    # cosy room light from above-front + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.4; s.data.angle = math.radians(10); s.data.color = srgb('#fff6e8')
    s.rotation_euler = Euler((math.radians(30), math.radians(-28), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 350; a.data.size = 8; a.data.color = srgb('#e8f0ff')
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

SEA_Y = 3.4        # shoreline (world y); sand below
FIELD = (-1.9, 1.9, -3.1, 2.6)   # where the watermelon may sit (x0, x1, y0, y1)

def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#bfe4f8'), 1)
    sand = noise_mat('sand', '#e4c890', '#f4e2b4', 40, 0.95, 0.35)
    nt = sand.node_tree; wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 9; wv.inputs['Distortion'].default_value = 3
    wv.bands_direction = 'Y'; tc = [n for n in nt.nodes if n.type == 'TEX_COORD'][0]; nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bp = [n for n in nt.nodes if n.type == 'BUMP'][0]; mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'ADD'
    nz = [n for n in nt.nodes if n.type == 'TEX_NOISE'][0]; nt.links.new(nz.outputs['Fac'], mx.inputs[0]); nt.links.new(wv.outputs['Fac'], mx.inputs[1]); nt.links.new(mx.outputs['Value'], bp.inputs['Height']); bp.inputs['Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2, 0)); f = bpy.context.object; f.scale = (14, 14, 1); f.data.materials.append(sand)
    wet = noise_mat('wetsand', '#c8b080', '#d8c090', 30, 0.4, 0.2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, SEA_Y + 0.4, 0.004)); f = bpy.context.object; f.scale = (14, 0.9, 1); f.data.materials.append(wet)
    sea = noise_mat('sea', '#2a9ad0', '#5ac4e8', 4, 0.15, 0.4, detail=4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, SEA_Y + 7.5, 0.03)); f = bpy.context.object; f.scale = (20, 14, 1); f.data.materials.append(sea)
    foam = mat('foam', '#ffffff', 0.6)
    random.seed(3)
    for i in range(16):
        x = -3.4 + i * 0.45; sphere((x, SEA_Y + 0.6 + random.uniform(-.05, .05), 0.03), (0.32, 0.07, 0.015), foam, 16, rot=(0, 0, random.uniform(-.2, .2)))
    for i in range(10):
        sphere((random.uniform(-3, 3), SEA_Y + random.uniform(1.6, 3.5), 0.05), (random.uniform(.2, .5), 0.03, 0.01), foam, 12)
    # parasol + mat at the upper right, bucket and spade at the left, shells, a pair of sandals
    pole = mat('pole', '#f4f0e8', 0.4); stripe_a = mat('pa', '#e85a4a', 0.6); stripe_b = mat('pb', '#fff8ec', 0.6)
    px, py = 1.9, 3.0
    cyl((px, py, 0.9), 0.04, 1.8, pole, 16)
    for k in range(8):
        a0 = k / 8 * math.tau
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.15, depth=0.35, location=(px, py, 1.85), rotation=(0, 0, a0 + math.pi / 8)); o = bpy.context.object
        o.scale = (1, 1, 1); o.data.materials.append(stripe_a if k % 2 else stripe_b)
    sphere((px, py, 2.05), (0.06, 0.06, 0.06), pole, 12)
    tw = (mat('towA', '#5ab0e0', 0.85), mat('towB', '#fff8ec', 0.85))
    for k in range(7):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(2.35 + (k - 3) * 0.2 * math.cos(0.15), 2.0 + (k - 3) * 0.2 * math.sin(0.15), 0.012)); o = bpy.context.object; o.scale = (0.2, 1.1, 0.02); o.rotation_euler = (0, 0, 0.15); o.data.materials.append(tw[k % 2])
    ball = (mat('bA', '#e85a4a', 0.35, 0.5), mat('bB', '#fff8ec', 0.35, 0.5), mat('bC', '#3a8ad0', 0.35, 0.5), mat('bD', '#f4c84a', 0.35, 0.5))
    for k in range(4):
        o = sphere((-2.05, -1.9, 0.22), (0.22, 0.22, 0.22), ball[k], 48); bm = bmesh.new(); bm.from_mesh(o.data)
        a0 = k * math.pi / 2; dl = [v for v in bm.verts if not (0 <= (math.atan2(v.co.y, v.co.x) - a0) % math.tau < math.pi / 2 + 0.03)]
        bmesh.ops.delete(bm, geom=dl, context='VERTS'); bm.to_mesh(o.data); bm.free()
    star = mat('star', '#f08a4a', 0.7)
    for k in range(5):
        a = k / 5 * math.tau + 0.3; sphere((2.2 + math.cos(a) * 0.09, -2.6 + math.sin(a) * 0.09, 0.02), (0.11, 0.035, 0.02), star, 12, rot=(0, 0, a))
    buck = mat('bucket', '#f4c84a', 0.4, 0.4); cyl((-2.0, 2.9, 0.18), 0.2, 0.36, buck, 32); cyl((-2.0, 2.9, 0.365), 0.17, 0.01, mat('bin', '#c89a2a', 0.5), 32)
    shell = mat('shell', '#f8d8d0', 0.5)
    for (x, y) in ((-1.6, -3.4), (1.2, -3.6), (-0.5, 3.0), (2.3, -1.2), (-2.3, 0.4)):
        sphere((x, y, 0.02), (0.09, 0.07, 0.03), shell, 16, rot=(0, 0, random.random() * 3))
    sand2 = mat('sandal', '#3a7ad0', 0.6)
    for s_ in (-1, 1): sphere((-1.9 + s_ * 0.13, -3.75, 0.02), (0.08, 0.2, 0.02), sand2, 16)
    render(sc, 'bg')
    META['field'] = [proj(FIELD[0], FIELD[3], 0), proj(FIELD[1], FIELD[2], 0)]
    META['origin'] = proj(0, 0, 0); META['ky'] = math.sin(math.radians(ELEV))
    META['start'] = proj(0, -3.6, 0)

def build_sprites():
    sc = reset(True)   # a striped watermelon
    m = bpy.data.materials.new('suika'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'RADIAL'
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 4; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = 16; nt.links.new(gr.outputs['Fac'], m1.inputs[0])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = 0.9; nt.links.new(nz.outputs['Fac'], m2.inputs[0]); nt.links.new(m1.outputs['Value'], m2.inputs[2])
    wv = nt.nodes.new('ShaderNodeMath'); wv.operation = 'PINGPONG'; wv.inputs[1].default_value = 0.5; nt.links.new(m2.outputs['Value'], wv.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.2; r.color_ramp.elements[1].position = 0.3
    r.color_ramp.elements[0].color = (*srgb('#76b84a'), 1); r.color_ramp.elements[1].color = (*srgb('#1f5a22'), 1)
    nt.links.new(wv.outputs['Value'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
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

SEA_Y = 3.4        # shoreline (world y); sand below
FIELD = (-1.9, 1.9, -3.1, 2.6)   # where the watermelon may sit (x0, x1, y0, y1)

def build_bg():
    sc = reset(False)
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#bfe4f8'), 1)
    sand = noise_mat('sand', '#e4c890', '#f4e2b4', 40, 0.95, 0.35)
    nt = sand.node_tree; wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 9; wv.inputs['Distortion'].default_value = 3
    wv.bands_direction = 'Y'; tc = [n for n in nt.nodes if n.type == 'TEX_COORD'][0]; nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bp = [n for n in nt.nodes if n.type == 'BUMP'][0]; mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'ADD'
    nz = [n for n in nt.nodes if n.type == 'TEX_NOISE'][0]; nt.links.new(nz.outputs['Fac'], mx.inputs[0]); nt.links.new(wv.outputs['Fac'], mx.inputs[1]); nt.links.new(mx.outputs['Value'], bp.inputs['Height']); bp.inputs['Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2, 0)); f = bpy.context.object; f.scale = (14, 14, 1); f.data.materials.append(sand)
    wet = noise_mat('wetsand', '#c8b080', '#d8c090', 30, 0.4, 0.2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, SEA_Y + 0.4, 0.004)); f = bpy.context.object; f.scale = (14, 0.9, 1); f.data.materials.append(wet)
    sea = noise_mat('sea', '#2a9ad0', '#5ac4e8', 4, 0.15, 0.4, detail=4)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, SEA_Y + 7.5, 0.03)); f = bpy.context.object; f.scale = (20, 14, 1); f.data.materials.append(sea)
    foam = mat('foam', '#ffffff', 0.6)
    random.seed(3)
    for i in range(16):
        x = -3.4 + i * 0.45; sphere((x, SEA_Y + 0.6 + random.uniform(-.05, .05), 0.03), (0.32, 0.07, 0.015), foam, 16, rot=(0, 0, random.uniform(-.2, .2)))
    for i in range(10):
        sphere((random.uniform(-3, 3), SEA_Y + random.uniform(1.6, 3.5), 0.05), (random.uniform(.2, .5), 0.03, 0.01), foam, 12)
    # parasol + mat at the upper right, bucket and spade at the left, shells, a pair of sandals
    pole = mat('pole', '#f4f0e8', 0.4); stripe_a = mat('pa', '#e85a4a', 0.6); stripe_b = mat('pb', '#fff8ec', 0.6)
    px, py = 1.9, 3.0
    cyl((px, py, 0.9), 0.04, 1.8, pole, 16)
    for k in range(8):
        a0 = k / 8 * math.tau
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.15, depth=0.35, location=(px, py, 1.85), rotation=(0, 0, a0 + math.pi / 8)); o = bpy.context.object
        o.scale = (1, 1, 1); o.data.materials.append(stripe_a if k % 2 else stripe_b)
    sphere((px, py, 2.05), (0.06, 0.06, 0.06), pole, 12)
    tw = (mat('towA', '#5ab0e0', 0.85), mat('towB', '#fff8ec', 0.85))
    for k in range(7):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(2.35 + (k - 3) * 0.2 * math.cos(0.15), 2.0 + (k - 3) * 0.2 * math.sin(0.15), 0.012)); o = bpy.context.object; o.scale = (0.2, 1.1, 0.02); o.rotation_euler = (0, 0, 0.15); o.data.materials.append(tw[k % 2])
    ball = (mat('bA', '#e85a4a', 0.35, 0.5), mat('bB', '#fff8ec', 0.35, 0.5), mat('bC', '#3a8ad0', 0.35, 0.5), mat('bD', '#f4c84a', 0.35, 0.5))
    for k in range(4):
        o = sphere((-2.05, -1.9, 0.22), (0.22, 0.22, 0.22), ball[k], 48); bm = bmesh.new(); bm.from_mesh(o.data)
        a0 = k * math.pi / 2; dl = [v for v in bm.verts if not (0 <= (math.atan2(v.co.y, v.co.x) - a0) % math.tau < math.pi / 2 + 0.03)]
        bmesh.ops.delete(bm, geom=dl, context='VERTS'); bm.to_mesh(o.data); bm.free()
    star = mat('star', '#f08a4a', 0.7)
    for k in range(5):
        a = k / 5 * math.tau + 0.3; sphere((2.2 + math.cos(a) * 0.09, -2.6 + math.sin(a) * 0.09, 0.02), (0.11, 0.035, 0.02), star, 12, rot=(0, 0, a))
    buck = mat('bucket', '#f4c84a', 0.4, 0.4); cyl((-2.0, 2.9, 0.18), 0.2, 0.36, buck, 32); cyl((-2.0, 2.9, 0.365), 0.17, 0.01, mat('bin', '#c89a2a', 0.5), 32)
    shell = mat('shell', '#f8d8d0', 0.5)
    for (x, y) in ((-1.6, -3.4), (1.2, -3.6), (-0.5, 3.0), (2.3, -1.2), (-2.3, 0.4)):
        sphere((x, y, 0.02), (0.09, 0.07, 0.03), shell, 16, rot=(0, 0, random.random() * 3))
    sand2 = mat('sandal', '#3a7ad0', 0.6)
    for s_ in (-1, 1): sphere((-1.9 + s_ * 0.13, -3.75, 0.02), (0.08, 0.2, 0.02), sand2, 16)
    render(sc, 'bg')
    META['field'] = [proj(FIELD[0], FIELD[3], 0), proj(FIELD[1], FIELD[2], 0)]
    META['origin'] = proj(0, 0, 0); META['ky'] = math.sin(math.radians(ELEV))
    META['start'] = proj(0, -3.6, 0)

def build_sprites():
    sc = reset(True)   # a striped watermelon
    m = bpy.data.materials.new('suika'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 3.2; wv.inputs['Distortion'].default_value = 7; wv.inputs['Detail'].default_value = 2; wv.inputs['Detail Scale'].default_value = 2.5
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, math.radians(90), 0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.45; r.color_ramp.elements[1].position = 0.6
    r.color_ramp.elements[0].color = (*srgb('#76b84a'), 1); r.color_ramp.elements[1].color = (*srgb('#1f5a22'), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.3; b.inputs['Specular IOR Level'].default_value = 0.5
    sphere((0, 0, 0.3), (0.34, 0.32, 0.3), m, 64)
    cyl((0, 0, 0.6), 0.015, 0.06, mat('stem', '#6a5a2a', 0.7), 8)
    sprite_cam(sc, 1.0, 160, 0.2); SPR['suika'] = {'res': 160, 'pxu': 160.0, 'base': [80.0, round(80 + 0.2 * math.cos(math.radians(ELEV)) * 160, 1)]}
    render(sc, 'suika')
    # cracked open: two halves falling apart with red flesh and seeds
    flesh = mat('flesh', '#f0384a', 0.5, 0.3); rind = mat('rind', '#e8f0c8', 0.6); seed = mat('seed', '#1a1210', 0.4)
    obs = [o for o in sc.objects if o.type == 'MESH']
    for o in obs: bpy.data.objects.remove(o)
    for s_ in (-1, 1):
        sp = sphere((0, 0, 0), (0.34, 0.32, 0.3), m, 64)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-s_ * 0.5, 0, 0)); cut = bpy.context.object; cut.scale = (1, 1, 1); cut.data.materials.append(flesh); cut.hide_render = True
        bo = sp.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.material_mode = 'TRANSFER'
        piv = bpy.data.objects.new('piv', None); bpy.context.collection.objects.link(piv); sp.parent = piv; cut.parent = piv
        cyl((-s_ * 0.002, 0, 0), 0.3, 0.006, rind, 48, rot=(0, math.radians(90), 0)).parent = piv
        cyl((-s_ * 0.006, 0, 0), 0.27, 0.006, flesh, 48, rot=(0, math.radians(90), 0)).parent = piv
        for k in range(9):
            a = k / 9 * math.tau; rr = 0.15 if k % 2 else 0.09
            sphere((-s_ * 0.012, math.cos(a) * rr, math.sin(a) * rr), (0.006, 0.018, 0.026), seed, 8).parent = piv
        piv.location = (s_ * 0.36, 0, 0.12); piv.rotation_euler = (0, s_ * math.radians(68), 0)
    for k in range(7):
        a = random.uniform(0, math.tau); sphere((math.cos(a) * 0.55, math.sin(a) * 0.4, 0.04), (0.06, 0.05, 0.03), flesh, 12)
    sprite_cam(sc, 1.6, 256, 0.2); SPR['crack'] = {'res': 256, 'pxu': 160.0, 'base': [128.0, round(128 + 0.2 * math.cos(math.radians(ELEV)) * 160, 1)]}
    render(sc, 'crack')
    sc = reset(True)   # the stick, lying along y (grip at +y)
    wd = wood('stick', '#c8925a', '#e0b07a')
    cyl((0, 0, 0), 0.045, 1.3, wd, 24, rot=(math.radians(90), 0, 0))
    cyl((0, 0.5, 0), 0.052, 0.3, mat('grip', '#d84a3a', 0.6), 24, rot=(math.radians(90), 0, 0))
    sprite_cam(sc, 1.6, 256, 0.0); SPR['stick'] = {'res': 256, 'pxu': 160.0, 'grip': [128.0, round(128 - 0.6 * math.sin(math.radians(ELEV)) * 160, 1)], 'tip': [128.0, round(128 + 0.65 * math.sin(math.radians(ELEV)) * 160, 1)]}
    render(sc, 'stick')
    sc = reset(True)   # calico cat sitting, facing us, the caller
    cw = mat('catw', '#fbf6ec', 0.85, 0.1, sss=0.2); co = mat('cato', '#e8a050', 0.85, 0.1); bk = mat('eye', '#1a1210', 0.9); pk = mat('catpk', '#f4a8a0', 0.8)
    sphere((0, 0.05, 0.3), (0.32, 0.28, 0.34), cw, 48)
    sphere((0, -0.05, 0.78), (0.3, 0.26, 0.26), cw, 48)
    sphere((-0.14, -0.08, 0.95), (0.13, 0.1, 0.08), co, 24)
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.1, depth=0.18, location=(s_ * 0.18, -0.02, 1.02)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.35, 0); e.data.materials.append(co if s_ < 0 else cw); smooth(e)
        sphere((s_ * 0.1, -0.29, 0.8), (0.035, 0.02, 0.045), bk, 12)
        sphere((s_ * 0.18, -0.25, 0.7), (0.05, 0.02, 0.03), pk, 12)
        sphere((s_ * 0.13, -0.2, 0.06), (0.08, 0.1, 0.05), cw, 16)
    sphere((0, -0.31, 0.73), (0.03, 0.02, 0.022), pk, 8)
    sphere((0.3, 0.2, 0.08), (0.2, 0.06, 0.05), co, 16, rot=(0, 0, 0.6))
    sprite_cam(sc, 1.4, 200, 0.5); SPR['cat'] = {'res': 200, 'pxu': 200 / 1.4}
    render(sc, 'cat')

JOBS = {'bg': build_bg, 'spr': build_sprites}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
