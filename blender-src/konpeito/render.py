# Renders the layers for konpeito.html from straight above: a copper pan in a clay hearth on a wooden counter (background),
# sugar sweets in four colours at three growth stages (grain, bumpy, full horns) and the syrup ladle.
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




CX, CY, PR = 360, 720, 300      # pan centre and inner radius in frame px

def W(px, py): return ((px - 360) / PXU, (640 - py) / PXU)

def copper():
    m = bpy.data.materials.new('copper'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#c87650'), 1); b.inputs['Metallic'].default_value = 0.35; b.inputs['Roughness'].default_value = 0.45
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45; nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def build_bg():
    sc = reset(False)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.6)); o = bpy.context.object; o.scale = (6, 10, 1); o.data.materials.append(noise_mat('counter', '#cfc4b2', '#ddd4c4', 10, 0.9, 0.2))
    cx, cy = W(CX, CY); r = PR / PXU
    # a round clay hearth (kamado) the pan sits in, with embers glowing in the gap
    clay = noise_mat('clay', '#b8876a', '#c99a7c', 8, 0.95, 0.5)
    cyl((cx, cy, -0.42), r + 0.55, 0.4, clay, 96)
    cyl((cx, cy, -0.19), r + 0.2, 0.04, mat('ember', '#3a1a10', 0.9, 0.0, emit=('#ff6a2a', 0.9)), 96)
    # the copper pan: a shallow bowl (hemisphere shell) with a rolled rim
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, location=(cx, cy, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.001], context='VERTS'); bm.to_mesh(o.data); bm.free()
    o.scale = (r + 0.05, r + 0.05, 0.14); smooth(o); o.modifiers.new('s', 'SOLIDIFY').thickness = 0.03; o.data.materials.append(copper())
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.06, minor_radius=0.05, major_segments=128, minor_segments=16, location=(cx, cy, 0.0))
    t = bpy.context.object; smooth(t); t.data.materials.append(copper())
    # a little tray for finished sweets and a paper label at the top
    tx, ty = W(360, 1180)
    box((tx, ty, -0.5), (3.9, 0.7, 0.1), wood('tray', '#c89a62', '#b88a52'), 0.04)
    box((tx, ty, -0.43), (3.7, 0.5, 0.04), mat('trayin', '#f4ecdc', 0.85), 0.01)
    sx, sy = W(360, 175)
    box((sx, sy, -0.5), (2.6, 0.62, 0.04), noise_mat('paper', '#fffaf0', '#f6efe2', 20, 0.95, 0.05), 0.01)
    render(sc, 'bg')
    META['pan'] = [CX, CY, PR]

def sugar(name, col):
    m = bpy.data.materials.new('su' + name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(col), 1); b.inputs['Roughness'].default_value = 0.42; b.inputs['Specular IOR Level'].default_value = 0.2
    b.inputs['Subsurface Weight'].default_value = 0.4; b.inputs['Subsurface Radius'].default_value = (0.6, 0.5, 0.45); b.inputs['Subsurface Scale'].default_value = 0.05
    return m

def build_ko(name, col, stage):
    sc = reset(True); top_cam(sc, 0.6, 96)
    m = sugar(name, col); R = 0.13 + 0.03 * stage
    o = sphere((0, 0, 0), (R, R, R), m, 32)
    if stage >= 1:
        tx = bpy.data.textures.new('kt' + name + str(stage), 'CLOUDS'); tx.noise_scale = 0.08
        d = o.modifiers.new('d', 'DISPLACE'); d.texture = tx; d.strength = 0.03 * stage
    if stage >= 1:
        n = 34 if stage == 2 else 20; L = 0.03 if stage == 2 else 0.016
        ga = math.pi * (3 - math.sqrt(5))
        for i in range(n):
            z = 1 - (i + 0.5) / n * 2; rr = math.sqrt(1 - z * z); a = i * ga
            v = Vector((math.cos(a) * rr, math.sin(a) * rr, z))
            if v.z < -0.3: continue
            loc = v * (R * 0.93)
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05 if stage == 2 else 0.04, radius2=0.022 if stage == 2 else 0.02, depth=L * 2, location=loc + v * L)
            c = bpy.context.object; c.rotation_euler = v.to_track_quat('Z', 'Y').to_euler(); smooth(c); c.data.materials.append(m)
            bv = c.modifiers.new('b', 'BEVEL'); bv.width = 0.008; bv.segments = 3; bv.limit_method = 'NONE'
    render(sc, f'ko_{name}{stage}')

def build_pot():
    sc = reset(True); top_cam(sc, 1.2, 200)
    # a small copper syrup ladle seen from above: bowl + long wooden handle
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, 0, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.001], context='VERTS'); bm.to_mesh(o.data); bm.free()
    o.scale = (0.2, 0.2, 0.12); smooth(o); o.modifiers.new('s', 'SOLIDIFY').thickness = 0.015; o.data.materials.append(copper())
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.015, location=(0, 0, 0)); t = bpy.context.object; smooth(t); t.data.materials.append(copper())
    sy = bpy.data.materials.new('syrup'); sy.use_nodes = True; b = sy.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#f6e6b8'), 1); b.inputs['Roughness'].default_value = 0.1; b.inputs['Coat Weight'].default_value = 0.6
    cyl((0, 0, -0.04), 0.18, 0.01, sy, 48)
    box((0.42, -0.16, 0.02), (0.5, 0.06, 0.04), wood('handle', '#c89a62', '#a87a48'), 0.02).rotation_euler = (0, 0, math.radians(-20))
    render(sc, 'pot')

COL = {'w': '#f8f4ee', 'p': '#f6a8c4', 'y': '#f6d65a', 'b': '#9ed2f2'}
JOBS = {'bg': build_bg, 'pot': build_pot}
for k, c in COL.items():
    for st in range(3): JOBS[f'{k}{st}'] = (lambda k=k, c=c, st=st: build_ko(k, c, st))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
