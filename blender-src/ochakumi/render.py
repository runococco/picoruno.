# Renders the layers for ochakumi.html. Every layer is rendered with the SAME full-frame camera
# (720x1280, 80 px per unit) so the game can stack them; build.py crops each to its bounding box.
# python3 render.py <what> <outdir>      what = all | bg,usu,mochi,usagi,kine,turner,plate (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 48.0; TZ = 0.9      # camera: ortho height 9.5 units, target (0,0,TZ)
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#efe4d0'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
    # moonlight key from upper right + warm lantern fill from the left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(25); s.data.color = srgb('#fff2dc')
    s.rotation_euler = Euler((math.radians(35), math.radians(-30), math.radians(-15)))
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 4))
    a = bpy.context.object; a.data.energy = 500; a.data.size = 5; a.data.color = srgb('#ffe6c4')
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

def glaze(name, c1, c2, inner='#f3ede0', scale=5, rough=0.35):
    m = noise_mat(name, c1, c2, scale, rough, 0.15, .4, .65)
    m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.45
    return m

# ---------------------------------------------------------------- parts
TRAY_Z = 0.06
CUP = {'rb': 0.27, 'rt': 0.35, 'h': 0.6, 'thk': 0.03}
CUPS = {   # glaze variants: outer colours
    'shiro': ('#ece6da', '#f6f1e6'), 'seiji': ('#9cc0ae', '#b6d4c2'), 'kiseto': ('#d9b45c', '#e8c977'),
    'oribe': ('#4f7a46', '#6a9a5a'), 'tenmoku': ('#3a2620', '#6a3e2a'),
}

def build_cup(kind):
    c1, c2 = CUPS[kind]
    outer = glaze('cup_' + kind, c1, c2); inner = mat('cup_in', '#f4efe4', 0.3, 0.45)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=CUP['rb'], depth=CUP['h'], location=(0, 0, TRAY_Z + CUP['h'] / 2), end_fill_type='NGON')
    o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    for v in bm.verts:
        if v.co.z > 0: v.co.x *= CUP['rt'] / CUP['rb']; v.co.y *= CUP['rt'] / CUP['rb']
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1], cuts=6)
    for v in bm.verts:   # gentle belly
        k = (v.co.z / CUP['h']) + 0.5; bulge = 1 + 0.06 * math.sin(k * math.pi)
        v.co.x *= bulge; v.co.y *= bulge
    bm.to_mesh(o.data); bm.free()
    o.data.materials.append(outer); o.data.materials.append(inner)
    so = o.modifiers.new('so', 'SOLIDIFY'); so.thickness = CUP['thk']; so.offset = -1; so.material_offset = 1; so.material_offset_rim = 1
    bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.012; bv.segments = 3; bv.limit_method = 'ANGLE'
    smooth(o)
    bpy.ops.mesh.primitive_torus_add(major_radius=CUP['rb'] * .8, minor_radius=0.025, location=(0, 0, TRAY_Z + 0.02))
    t = bpy.context.object; t.data.materials.append(mat('foot', '#c9a882', 0.8, 0.1)); smooth(t)
    if kind == 'shiro':   # a little blue brush line
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.012, location=(0, 0, TRAY_Z + CUP['h'] * .78))
        t = bpy.context.object; t.scale = (CUP['rt'] * 1.0 + .012, CUP['rt'] * 1.0 + .012, 1); t.data.materials.append(mat('gosu', '#3a5a9a', 0.4, 0.3))

KY = (0.0, 0.4, 2.15)   # kyusu body centre
def build_kyusu():
    clay = noise_mat('shudei', '#a8482a', '#bd5a34', 25, 0.45, 0.08, .4, .7)
    clay.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.35
    x, y, z = KY
    body = sphere((x, y, z), (0.5, 0.5, 0.4), clay, 64)
    for v in body.data.vertices:
        if v.co.z < -0.55: v.co.z = -0.55     # flat bottom
    sphere((x, y, z + 0.34), (0.36, 0.36, 0.1), clay, 48)                    # lid
    sphere((x, y, z + 0.46), (0.07, 0.07, 0.07), clay, 24)                   # knob
    bpy.ops.mesh.primitive_torus_add(major_radius=0.37, minor_radius=0.015, location=(x, y, z + 0.31))
    bpy.context.object.data.materials.append(mat('lidgap', '#5a2414', 0.8, 0.1))
    # spout: tapered tube curving up to the right
    pts = [Vector((x + 0.42, y, z - 0.08)), Vector((x + 0.62, y, z + 0.0)), Vector((x + 0.78, y, z + 0.2))]
    for i in range(30):
        u = i / 29; p = pts[0].lerp(pts[1], u * 2) if u < .5 else pts[1].lerp(pts[2], (u - .5) * 2)
        sphere(p, (0.11 - 0.055 * u,) * 3, clay, 24)
    # side handle (yokode) toward the viewer, slightly to the left
    hd = Vector((-0.62, -0.62, 0.06)).normalized()
    a0 = Vector((x, y, z - 0.02)) + hd * 0.42; a1 = a0 + hd * 0.62
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=(a1 - a0).length, location=(a0 + a1) / 2)
    hcyl = bpy.context.object; hcyl.rotation_euler = (a1 - a0).to_track_quat('Z', 'Y').to_euler(); hcyl.data.materials.append(clay); smooth(hcyl)
    sphere(a1, (0.085, 0.085, 0.085), clay, 24)
    return Vector((x + 0.8, y, z + 0.24))

def build_bg():
    sc = reset(False)
    # tatami
    tat = bpy.data.materials.new('tatami'); tat.use_nodes = True; nt = tat.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 0.5
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (*srgb('#b8a868'), 1); r.color_ramp.elements[1].color = (*srgb('#cdbd7c'), 1)
    nt.links.new(wv.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.3; nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); p = bpy.context.object; p.scale = (9, 14, 1); p.data.materials.append(tat)
    heri = noise_mat('heri', '#2e3a2a', '#3a4a34', 80, 0.85, 0.3)
    for yy in (-3.2, 2.6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, yy, 0.005)); h = bpy.context.object; h.scale = (9, 0.14, 0.01); h.data.materials.append(heri)
    # shoji wall at the back, soft daylight behind the paper
    paper = mat('shoji', '#f6f1e4', 0.9, 0.0, emit=('#fff6e0', 0.35))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.2, 2.5)); w = bpy.context.object; w.scale = (9, 0.05, 5); w.data.materials.append(paper)
    fr = wood('shojiframe', '#8a6a48', '#9a7a56')
    for i in range(-6, 7):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 0.6, 4.15, 2.5)); f = bpy.context.object; f.scale = (0.04, 0.04, 5); f.data.materials.append(fr)
    for k in range(9):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.15, 0.25 + k * 0.6)); f = bpy.context.object; f.scale = (9, 0.04, 0.04); f.data.materials.append(fr)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.1, 0.08)); f = bpy.context.object; f.scale = (9, 0.12, 0.16); f.data.materials.append(fr)
    # long tray (shunkei lacquer), cups are drawn on it in-game
    lac = wood('shunkei', '#a85c22', '#b2652a'); lac.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.25
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.03)); t = bpy.context.object; t.scale = (4.3, 1.25, 0.06); t.data.materials.append(lac); bevel(t, 0.03)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.065)); cut = bpy.context.object; cut.scale = (4.15, 1.1, 0.06); cut.hide_render = True
    bo = t.modifiers.new('b', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    # wagashi on a small plate (front left) and a tea caddy (back right)
    pl = mat('plate', '#f4f0e8', 0.3, 0.4)
    cyl((1.45, -2.75, 0.03), 0.42, 0.05, pl, 48)
    for (dx, col) in ((-0.15, '#f4b8c4'), (0.18, '#c8e0a8')):
        o = sphere((1.45 + dx, -2.75, 0.16), (0.17, 0.17, 0.12), mat('nerikiri' + col, col, 0.7, 0.1, sss=0.3), 32)
    nat = mat('natsume', '#1e1412', 0.18, 0.6)
    o = sphere((1.6, 1.55, 0.25), (0.3, 0.3, 0.26), nat, 48)
    for v in o.data.vertices:
        if v.co.z < -0.7: v.co.z = -0.7
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.01, location=(1.6, 1.55, 0.3)); bpy.context.object.data.materials.append(mat('gold', '#d8a840', 0.3, 0.6))
    render(sc, 'bg')

def only(fn, name):
    sc = reset(); r = fn(); render(sc, name); return r

JOBS = {'bg': build_bg, 'kyusu': lambda: only(build_kyusu, 'kyusu')}
for k in CUPS: JOBS['cup_' + k] = (lambda k=k: only(lambda: build_cup(k), 'cup_' + k))
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
tip = Vector((KY[0] + 0.8, KY[1], KY[2] + 0.24))
meta = {'pxu': PXU, 'elev': ELEV, 'tz': TZ, 'trayZ': TRAY_Z, 'cup': CUP, 'origin': proj(0, 0, 0),
        'kyusu': proj(*KY), 'tip': proj(*tip), 'cups': list(CUPS)}
json.dump(meta, open(os.path.join(OUT, 'scene.json'), 'w'))
