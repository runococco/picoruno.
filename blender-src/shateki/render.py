# Renders the layers for shateki.html: the festival shooting stall (full frame) and the prize / cork-gun sprites
# (same nearly level camera angle, anchors recorded in scene.json).
# python3 render.py <what> <outdir>
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 8.0; ELEV = 8.0; TZ = 3.2      # ortho height 8 units, nearly level
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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#ffe8cc'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
    # summer-night stall: warm lantern light from the front + soft fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.6; s.data.angle = math.radians(25); s.data.color = srgb('#fff0d8')
    s.rotation_euler = Euler((math.radians(50), math.radians(30), math.radians(25)))
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

SHELF_Z = (4.15, 3.05, 1.95)      # top surface of each tier
SHELF_Y = (1.2, 0.6, 0.0)         # tiers step toward the camera

def build_bg():
    sc = reset(False)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#2a2440'), 1); w.inputs[1].default_value = 0.6
    # red/white striped back curtain
    red = mat('cred', '#c8323a', 0.85, 0.1); wh = mat('cwh', '#f6eee0', 0.85, 0.1)
    for k in range(-12, 13):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.17, depth=7.5, location=(k * 0.32, 2.2 + (k % 2) * 0.05, 3.6)); o = bpy.context.object
        o.scale = (1, 0.45, 1); o.data.materials.append(red if (k // 2) % 2 == 0 else wh); smooth(o)
    # tiers covered in red felt
    felt = noise_mat('felt', '#b82a34', '#c8343e', 40, 0.95, 0.2)
    for z, y in zip(SHELF_Z, SHELF_Y):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y + 0.3, z - 0.4)); o = bpy.context.object; o.scale = (5.6, 0.9, 0.8); o.data.materials.append(felt); bevel(o, 0.03, 3)
    gold = mat('trim', '#e8b840', 0.35, 0.6)
    for z, y in zip(SHELF_Z, SHELF_Y):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y - 0.16, z - 0.03)); o = bpy.context.object; o.scale = (5.6, 0.04, 0.06); o.data.materials.append(gold)
    # wooden frame of the stall + counter at the front
    wd = wood('frame', '#a8784a', '#8a5a32')
    for x in (-2.75, 2.75):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -0.4, 3.4)); o = bpy.context.object; o.scale = (0.24, 0.24, 7.6); o.data.materials.append(wd); bevel(o, 0.02, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.4, 6.75)); o = bpy.context.object; o.scale = (6, 0.3, 0.4); o.data.materials.append(wd)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.6, 0.25)); o = bpy.context.object; o.scale = (6, 1.2, 0.5); o.data.materials.append(wd); bevel(o, 0.03, 2)
    cloth = noise_mat('counter', '#2a5aa8', '#3468b8', 30, 0.95, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.25, -0.5)); o = bpy.context.object; o.scale = (6, 0.05, 1.1); o.data.materials.append(cloth)
    # noren banner at the top with lanterns
    nr = mat('noren', '#f6eee0', 0.9, 0.1)
    for k in range(-4, 5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(k * 0.6, -0.65, 6.25)); o = bpy.context.object; o.scale = (0.56, 0.02, 0.5); o.data.materials.append(nr)
    lan = mat('lantern', '#ffb050', 0.6, 0.1, emit=('#ffa040', 2.2)); blk = mat('lanblk', '#2a1a10', 0.7)
    for x in (-2.1, -0.7, 0.7, 2.1):
        sphere((x, -0.9, 5.62), (0.24, 0.24, 0.28), lan, 32)
        for dz in (-0.27, 0.27): cyl((x, -0.9, 5.62 + dz), 0.11, 0.06, blk, 16)
        bpy.ops.object.light_add(type='POINT', location=(x, -1.4, 5.3)); l = bpy.context.object; l.data.energy = 60; l.data.color = srgb('#ffb060'); l.data.shadow_soft_size = 0.4
    render(sc, 'bg')
    META['shelves'] = [proj(0, y - 0.0, z)[1] for z, y in zip(SHELF_Z, SHELF_Y)]
    META['counter'] = proj(0, -1.6, 0.5)[1]

def prize_cam(sc, name, h):
    to2d = sprite_cam(sc, max(0.8, h * 1.35), 256, h / 2)
    SPR[name] = {'res': 256, 'pxu': 256 / max(0.8, h * 1.35), 'base': to2d(0, 0), 'h': h}
    render(sc, name)

def BK(): return mat('pk', '#1a1210', 0.9)

def build_prizes():
    # beckoning cat
    sc = reset(True); wh = mat('pw', '#fbf6ec', 0.5, 0.3); rd = mat('pr', '#d8402e', 0.4, 0.4); gd = mat('pg', '#e8b840', 0.3, 0.6); bk = None
    def cat(body, ear, deco, h=0.5):
        sphere((0, 0, 0.17), (0.17, 0.14, 0.17), body, 32); sphere((0, -0.01, 0.38), (0.16, 0.14, 0.13), body, 32)
        for s_ in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.055, depth=0.1, location=(s_ * 0.1, 0, 0.5)); e = bpy.context.object; e.rotation_euler = (0, s_ * 0.35, 0); e.data.materials.append(ear); smooth(e)
            sphere((s_ * 0.055, -0.13, 0.4), (0.02, 0.01, 0.022), BK(), 12)
        sphere((0.14, -0.04, 0.43), (0.05, 0.05, 0.07), body, 16)   # raised paw
        cyl((0, 0, 0.29), 0.13, 0.025, mat('pr', '#d8402e', 0.4, 0.4), 32); sphere((0, -0.13, 0.26), (0.03, 0.02, 0.03), deco, 12)
        sphere((0, -0.06, 0.12), (0.08, 0.04, 0.06), deco, 16)
    cat(wh, rd, gd); prize_cam(sc, 'neko', 0.55)
    sc = reset(True); g2 = mat('gold2', '#e8b030', 0.25, 0.8); g2.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.6
    cat(g2, g2, mat('pr2', '#d8402e', 0.4, 0.4)); prize_cam(sc, 'kinneko', 0.55)
    # bear plush
    sc = reset(True); br = noise_mat('fur', '#b07a4a', '#c08a58', 60, 0.95, 0.3); mz = mat('muz', '#f0d8b0', 0.9); rb = mat('ribbon', '#4a7ad8', 0.6)
    sphere((0, 0, 0.17), (0.17, 0.14, 0.18), br, 32); sphere((0, 0, 0.42), (0.15, 0.13, 0.14), br, 32)
    for s_ in (-1, 1):
        sphere((s_ * 0.11, 0, 0.54), (0.055, 0.04, 0.055), br, 16); sphere((s_ * 0.06, -0.12, 0.45), (0.018, 0.01, 0.02), BK(), 12)
        sphere((s_ * 0.12, -0.06, 0.04), (0.06, 0.07, 0.05), br, 16); sphere((s_ * 0.17, -0.02, 0.2), (0.05, 0.05, 0.08), br, 16)
    sphere((0, -0.12, 0.39), (0.06, 0.03, 0.045), mz, 16); sphere((0, -0.15, 0.4), (0.018, 0.01, 0.014), BK(), 8)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.02, location=(0, 0, 0.31)); t = bpy.context.object; t.data.materials.append(rb)
    prize_cam(sc, 'kuma', 0.6)
    # candy box
    sc = reset(True); bx = mat('box', '#f0c840', 0.6, 0.2); bs = mat('boxs', '#d8402e', 0.6, 0.2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.21)); o = bpy.context.object; o.scale = (0.28, 0.12, 0.42); o.data.materials.append(bx); bevel(o, 0.01, 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.061, 0.24)); o = bpy.context.object; o.scale = (0.2, 0.004, 0.14); o.data.materials.append(bs)
    sphere((0, -0.066, 0.24), (0.05, 0.005, 0.05), mat('boxw', '#fbf6ec', 0.6), 16)
    prize_cam(sc, 'hako', 0.42)
    # ramune bottle
    sc = reset(True); gl = bpy.data.materials.new('glass'); gl.use_nodes = True; b = gl.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb('#8ad0e8'), 1); b.inputs['Transmission Weight'].default_value = 0.85; b.inputs['Roughness'].default_value = 0.08; b.inputs['IOR'].default_value = 1.45
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.075, depth=0.3, location=(0, 0, 0.15)); o = bpy.context.object; o.data.materials.append(gl); smooth(o); bevel(o, 0.02, 3)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.075, radius2=0.035, depth=0.12, location=(0, 0, 0.36)); o = bpy.context.object; o.data.materials.append(gl); smooth(o)
    cyl((0, 0, 0.44), 0.036, 0.06, mat('cap', '#3a8ad8', 0.4, 0.4), 24)
    sphere((0, 0, 0.36), (0.028, 0.028, 0.028), mat('marble', '#d0f0f8', 0.05, 0.8), 16)
    prize_cam(sc, 'ramune', 0.48)
    # spinning top
    sc = reset(True); kw = wood('koma', '#e8c890', '#d0a868')
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.15, depth=0.16, location=(0, 0, 0.09)); o = bpy.context.object; o.rotation_euler = (math.radians(180), 0, 0); o.data.materials.append(kw); smooth(o)
    for i, (c, z) in enumerate((('#d8402e', 0.17), ('#3a8a4a', 0.185), ('#3a72c0', 0.2))): cyl((0, 0, z), 0.15 - i * 0.03, 0.02, mat(f'kr{i}', c, 0.5, 0.3), 48)
    cyl((0, 0, 0.26), 0.02, 0.1, kw, 16)
    prize_cam(sc, 'koma', 0.3)
    # tin duck
    sc = reset(True); yl = mat('duck', '#f0c838', 0.35, 0.5); bl = mat('beak', '#e87a2a', 0.5, 0.3)
    sphere((0, 0, 0.12), (0.17, 0.12, 0.11), yl, 32); sphere((-0.08, 0, 0.27), (0.08, 0.075, 0.08), yl, 32)
    sphere((-0.17, 0, 0.26), (0.05, 0.03, 0.02), bl, 16); sphere((-0.1, -0.07, 0.29), (0.015, 0.01, 0.016), BK(), 8)
    sphere((0.15, 0, 0.18), (0.05, 0.04, 0.04), yl, 16)
    prize_cam(sc, 'ahiru', 0.36)
    # cork
    sc = reset(True); ck = noise_mat('cork', '#c89a5a', '#a87a40', 50, 0.95, 0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.08, radius2=0.065, depth=0.12, location=(0, 0, 0)); o = bpy.context.object; o.data.materials.append(ck); smooth(o); bevel(o, 0.01, 2)
    o.rotation_euler = (math.radians(70), 0, 0)
    sprite_cam(sc, 0.3, 96); SPR['cork'] = {'res': 96}
    render(sc, 'cork')

def build_gun():
    sc = reset(True)
    wd = wood('stock', '#a86a3a', '#8a522a'); mt = mat('barrel', '#3a3a42', 0.35, 0.6)
    # seen from behind and above: the barrel points into the screen
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.5, 0)); s = bpy.context.object; s.scale = (0.2, 0.9, 0.16); s.data.materials.append(wd); bevel(s, 0.04, 4)
    cyl((0, 0.35, 0.03), 0.045, 1.1, mt, 24, (math.radians(90), 0, 0))
    cyl((0, 0.9, 0.03), 0.06, 0.06, mt, 24, (math.radians(90), 0, 0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.95, -0.02)); b = bpy.context.object; b.scale = (0.18, 0.25, 0.22); b.data.materials.append(wd); bevel(b, 0.05, 4)
    bpy.ops.object.empty_add(location=(0, 0, 0)); piv = bpy.context.object
    for o in list(sc.objects):
        if o.type == 'MESH': o.parent = piv
    piv.rotation_euler.x = math.radians(45)
    e = math.radians(ELEV); sc_ = sc
    to2d = sprite_cam(sc, 2.4, 384, 0.0)
    SPR['gun'] = {'res': 384, 'pxu': 384 / 2.4}
    render(sc, 'gun')

JOBS = {'bg': build_bg, 'prizes': build_prizes, 'gun': build_gun}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
MP = os.path.join(OUT, 'scene.json')
meta = json.load(open(MP)) if os.path.exists(MP) else {}
meta.update(META); meta['spr'] = {**meta.get('spr', {}), **SPR}; meta['pxu'] = PXU
json.dump(meta, open(MP, 'w'))
