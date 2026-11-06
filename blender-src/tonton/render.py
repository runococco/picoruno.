# Renders the layers for tonton.html: a low table with a paper sumo box (ring printed on top) in a tatami room,
# and flat paper-cutout cat wrestlers seen from the side (front ortho).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 14.0; TZ = 0.0      # almost level: frame row ~ 640 - z * 160
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
    # clear winter daylight from above-left + sky fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(20); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(25), math.radians(-15), math.radians(0)))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 8; a.data.color = srgb('#ffe8d0')
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

BOX_Z = -0.9; BOX = (3.8, 2.2)

def build_bg():
    sc = reset(False)
    # back wall (plaster + wainscot) and tatami floor far behind; a low wooden table in front
    plaster = noise_mat('plaster', '#efe2c8', '#f6ead4', 8, 0.95, 0.15)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, 2), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (12, 14, 1); o.data.materials.append(plaster)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 5.9, -2.5)); o = bpy.context.object; o.scale = (12, 0.1, 3); o.data.materials.append(wood('wains', '#a87a4a', '#b88a58'))
    # a hanging scroll with a big round brush circle (enso)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 5.8, 2.4)); o = bpy.context.object; o.scale = (1.4, 0.02, 2.6); o.data.materials.append(mat('scroll', '#f8f0dc', 0.9))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.05, location=(0, 5.78, 2.6), rotation=(math.radians(90), 0, 0)); o = bpy.context.object; o.scale = (1, 1, 0.3); o.data.materials.append(mat('ink', '#3a3438', 0.9))
    for z in (1.1, 3.7): cyl((0, 5.76, z), 0.05, 1.6, wood('rod', '#6a4428', '#7a5232'), 16, rot=(0, math.radians(90), 0))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -14, -2.6)); o = bpy.context.object; o.scale = (14, 40, 1); o.data.materials.append(noise_mat('tatami', '#c8c088', '#d4cc96', 40, 0.9, 0.3, detail=2))
    table = wood('table', '#8a5a32', '#9a6a3e')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -1.95)); o = bpy.context.object; o.scale = (6, 4.5, 0.3); o.data.materials.append(table); bevel(o, 0.05)
    # the paper sumo box: kraft-paper sides, a printed ring on top
    kraft = noise_mat('kraft', '#c8a070', '#d4ac7c', 30, 0.9, 0.15)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, (BOX_Z - 1.8) / 2)); o = bpy.context.object; o.scale = (BOX[0], BOX[1], BOX_Z + 1.8); o.data.materials.append(kraft); bevel(o, 0.02)
    topm = noise_mat('boxtop', '#e8d4a4', '#f0dcb0', 30, 0.9, 0.1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, BOX_Z + 0.005)); o = bpy.context.object; o.scale = (BOX[0] - 0.04, BOX[1] - 0.04, 0.01); o.data.materials.append(topm)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.035, location=(0, 0, BOX_Z + 0.012)); o = bpy.context.object; o.scale = (1, BOX[1] / 3.2, 0.2); o.data.materials.append(mat('ringline', '#8a3a2a', 0.9))
    for s_ in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(s_ * 0.3, 0, BOX_Z + 0.012)); o = bpy.context.object; o.scale = (0.05, 0.4, 0.004); o.data.materials.append(mat('shikiri', '#fffaf0', 0.9))
    # tassels hanging from the box corners (red, blue, white, black)
    for (x, c) in ((-1.95, '#d84a4a'), (1.95, '#3a6ab8')):
        cyl((x, -1.15, BOX_Z - 0.35), 0.06, 0.5, mat('tas' + c, c, 0.9), 16); sphere((x, -1.15, BOX_Z - 0.05), (0.08, 0.08, 0.08), mat('tas' + c, c, 0.9), 16)
    # the cat referee's fan on the table
    render(sc, 'bg')
    META['ring'] = [proj(-1.5, 0, BOX_Z), proj(1.5, 0, BOX_Z)]; META['top'] = proj(0, 0, BOX_Z); META['boxL'] = proj(-BOX[0] / 2, -BOX[1] / 2, BOX_Z); META['boxR'] = proj(BOX[0] / 2, -BOX[1] / 2, BOX_Z)

WR = (('tora', '#f0b060', '#d07a30', '#3a6ab8'), ('shiro', '#fbf6ec', None, '#d84a4a'), ('saba', '#b8bcc4', '#6a6e78', '#8a5aa8'), ('hachi', '#fbf6ec', '#3a363c', '#2a8a6a'), ('mike', '#fbf6ec', '#e8a050', '#c89a2a'))

def build_wrestlers():
    for name, fur, pat, belt in WR:
        sc = reset(True)   # a flat paper-cutout cat wrestler in profile, facing right, crouched with paws forward
        paper = mat('pp' + name, fur, 0.95, 0.05); pm = mat('pt' + name, pat, 0.95, 0.05) if pat else paper; bm = mat('belt' + name, belt, 0.9)
        blk = mat('eye', '#1a1210', 0.9); edge = mat('edge', '#e8dcc0', 0.95)
        D = 0.02
        sphere((0, 0, 0.42), (0.36, D, 0.36), paper, 64)                                   # body
        sphere((0.32, -0.002, 0.82), (0.26, D, 0.23), paper, 64)                          # head forward
        for (x, z, r) in ((0.24, 1.02, 0.1), (0.42, 1.0, 0.1)):
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=r, depth=D * 2, location=(x, 0, z), rotation=(math.radians(90), 0, math.radians(30))); e = bpy.context.object; e.data.materials.append(paper)
        sphere((0.46, -0.025, 0.86), (0.035, 0.005, 0.04), blk, 16)                       # eye
        sphere((0.58, -0.02, 0.78), (0.03, 0.004, 0.025), mat('nose', '#e88a8a', 0.8), 12)
        sphere((0.42, -0.003, 0.5), (0.26, D, 0.08), paper, 32); e = bpy.context.object; e.rotation_euler = (0, math.radians(-20), 0)   # arm thrust forward
        sphere((0.66, -0.004, 0.58), (0.07, D, 0.07), paper, 16)
        if pat: sphere((-0.1, -0.025, 0.6), (0.18, 0.005, 0.14), pm, 32); sphere((0.26, -0.025, 0.95), (0.1, 0.005, 0.08), pm, 24)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.026, 0.28)); o = bpy.context.object; o.scale = (0.74, 0.004, 0.14); o.data.materials.append(bm)   # mawashi
        for x in (-0.18, 0.18): sphere((x, -0.002, 0.08), (0.11, D, 0.09), paper, 24)    # feet
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.06, 0.012)); o = bpy.context.object; o.scale = (0.7, 0.12, 0.024); o.data.materials.append(edge)   # folded paper base
        bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); tl = bpy.context.object; tl.data.bevel_depth = 0.03; tl.data.dimensions = '3D'
        bp = tl.data.splines[0].bezier_points; bp[0].co = (-0.32, 0, 0.42); bp[1].co = (-0.55, 0, 0.75)
        for p in bp: p.handle_left_type = p.handle_right_type = 'AUTO'
        tl.data.materials.append(pm if pat else paper)
        pt = side_cam(sc, 1.6, 256, 0.5); SPR['wr'] = {'res': 256, 'pxu': 160.0, 'foot': pt(0, 0.0), 'nose': pt(0.66, 0.5), 'back': pt(-0.36, 0.42)}
        render(sc, 'wr_' + name)

JOBS = {'bg': build_bg, 'wr': build_wrestlers}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
