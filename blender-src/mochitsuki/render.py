# Renders the layers for mochitsuki.html. Every layer is rendered with the SAME full-frame camera
# (720x1280, 80 px per unit) so the game can stack them; build.py crops each to its bounding box.
# python3 render.py <what> <outdir>      what = all | bg,usu,mochi,usagi,kine,turner,plate (comma list)
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)
RES = (720, 1280); SCALE = 9.5; ELEV = 16.0; TZ = 2.9      # camera: ortho height 9.5 units, target (0,0,TZ)
PXU = RES[1] / SCALE

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
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#3a4677'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    # moonlight key from upper right + warm lantern fill from the left
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 2.2; s.data.angle = math.radians(18); s.data.color = srgb('#dfe6ff')
    s.rotation_euler = Euler((math.radians(45), math.radians(25), math.radians(20)))
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 4))
    a = bpy.context.object; a.data.energy = 900; a.data.size = 4; a.data.color = srgb('#ffcf96')
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

# ---------------------------------------------------------------- scene parts
USU = (0.0, 0.3, 0.0)          # mortar base centre
USU_TOP = 1.25                  # rim height
MOCHI_Z = 1.18
PIVOT = (-1.27, 0.2, 1.85)      # where rabbit A holds the mallet

def build_usu():
    m = wood('usu', '#8a5a3a', '#a8714a')
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.95, depth=USU_TOP, location=(USU[0], USU[1], USU_TOP / 2))
    o = bpy.context.object; o.data.materials.append(m); smooth(o)
    for v in o.data.vertices:   # waisted drum shape
        z = v.co.z / (USU_TOP / 2); k = 1 - 0.13 * (1 - z * z); v.co.x *= k; v.co.y *= k
    bevel(o, 0.06)
    # hollow
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(USU[0], USU[1], USU_TOP + 0.05))
    cut = bpy.context.object; cut.scale = (0.72, 0.72, 0.5); cut.hide_render = True
    bo = o.modifiers.new('bool', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    # iron band
    bpy.ops.mesh.primitive_torus_add(major_radius=0.86, minor_radius=0.035, location=(USU[0], USU[1], 0.25))
    t = bpy.context.object; t.data.materials.append(mat('band', '#3a3330', 0.6)); smooth(t)

def build_mochi(state):
    m = noise_mat('mochi%d' % state, '#efe9dc', '#fbf8f1', [40, 25, 6][state], [0.85, 0.7, 0.5][state], [1.2, 0.6, 0.08][state])
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Scale'].default_value = 0.1
    o = sphere((USU[0], USU[1], MOCHI_Z), (0.66, 0.66, [0.3, 0.27, 0.25][state]), m, 64)
    if state < 2:   # rough steamed rice: displaced lumps + grains
        s = o.modifiers.new('s', 'SUBSURF'); s.levels = s.render_levels = 2
        t = bpy.data.textures.new('lump', 'CLOUDS'); t.noise_scale = [0.08, 0.18][state]
        d = o.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = [0.07, 0.04][state]; d.texture_coords = 'OBJECT'
    if state == 2:
        # finished mochi gets a happy face
        face(USU[0], USU[1] - 0.6, MOCHI_Z + 0.1, 1.2, tilt=True)

def face(x, y, z, s=1.0, closed=False, tilt=False, ouch=False):
    blk = mat('eye', (0.02, 0.015, 0.012), 1.0, 0.0); pnk = mat('cheek', '#f2a0a0', 1.0, 0.0)
    for sx in (-1, 1):
        if ouch:   # > <
            for k in (-1, 1):
                bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.012 * s, depth=0.09 * s, location=(x + sx * 0.08 * s, y, z + k * 0.018 * s), rotation=(0, math.radians(90 + sx * k * 30), 0))
                bpy.context.object.data.materials.append(blk)
        else:
            sphere((x + sx * 0.08 * s, y, z), (0.034 * s, 0.015, 0.034 * s), blk, 20)
        sphere((x + sx * 0.15 * s, y + 0.004, z - 0.055 * s), (0.04 * s, 0.01, 0.024 * s), pnk, 16)

def rabbit(x, color, lean, pose='idle', name='r'):
    """Round rabbit facing the camera. pose: hold (paws up holding mallet) / idle / reach / ouch."""
    body = mat('fur_' + color, color, 0.95, 0.1, sss=0.15)
    inner = mat('ear_in', '#f4b7c0', 0.95)
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    root.location = (x, 0.4, 0); root.rotation_euler = (0, 0, math.radians(lean))
    sphere((0, 0, 0.62), (0.62, 0.55, 0.62), body, 48, parent=root)          # body
    sphere((0, -0.05, 1.42), (0.5, 0.45, 0.44), body, 48, parent=root)       # head
    ear_tilt = -0.35 if pose == 'ouch' else 0.0
    for s in (-1, 1):
        e = sphere((s * 0.2, 0.0, 2.02), (0.11, 0.08, 0.38), body, 32, (ear_tilt * 2.5 if pose == 'ouch' else 0, s * 0.18 + (s * 0.9 if pose == 'ouch' else 0), 0), root)
        sphere((s * 0.2, -0.05, 2.02), (0.06, 0.04, 0.27), inner, 24, e.rotation_euler, root)
        if pose == 'ouch':
            e.location = (s * 0.42, 0.0, 1.78); root.children[-1].location = (s * 0.42, -0.05, 1.78)
        sphere((s * 0.3, -0.25, 0.08), (0.17, 0.22, 0.09), body, 24, parent=root)   # feet
    sphere((0, 0.5, 0.45), (0.16, 0.16, 0.16), body, 24, parent=root)           # tail
    # face (children so they follow the lean)
    before = set(bpy.data.objects)
    face(0, -0.505, 1.42, 1.15, ouch=(pose == 'ouch'))
    sphere((0, -0.52, 1.35), (0.03, 0.015, 0.022), mat('nose', '#d9707e', 0.9), 16)
    for o in set(bpy.data.objects) - before:
        o.parent = root      # created at root-local coordinates
    # arms
    if pose == 'hold':
        sphere((0.42, -0.36, 1.36), (0.12, 0.12, 0.42), body, 24, (0, math.radians(28), 0), root)
        sphere((0.56, -0.48, 1.78), (0.14, 0.13, 0.13), mat('paw', '#f4d0d4', 0.95), 24, (0, 0, 0), root)
        sphere((-0.4, -0.35, 0.72), (0.12, 0.13, 0.2), body, 24, (0, math.radians(-20), 0), root)
    elif pose == 'reach':
        sphere((-0.3, -0.35, 0.72), (0.12, 0.13, 0.2), body, 24, (0, math.radians(-20), 0), root)
        a = sphere((-0.85, -0.3, 1.18), (0.6, 0.13, 0.13), body, 24, (0, math.radians(14), 0), root)
        sphere((-1.42, -0.3, 1.36), (0.15, 0.14, 0.11), mat('paw', '#f4d0d4', 0.95), 24, (0, 0, 0), root)
    else:
        for s in (-1, 1): sphere((s * 0.4, -0.35, 0.72), (0.12, 0.13, 0.2), body, 24, (0, math.radians(s * 20), 0), root)
    return root

def build_kine():
    """Mallet lying along +X from the pivot (handle end) — the game rotates it around PIVOT."""
    m = wood('kine', '#9a6a44', '#b5845a')
    L = 1.27
    cyl((PIVOT[0] + L / 2 - 0.1, PIVOT[1] - 0.6, PIVOT[2]), 0.06, L, m, 24, (0, math.radians(90), 0))
    h = cyl((PIVOT[0] + L, PIVOT[1] - 0.6, PIVOT[2]), 0.25, 0.85, m, 48, (0, 0, 0))
    bevel(h, 0.05)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.025, location=(PIVOT[0] + L, PIVOT[1] - 0.6, PIVOT[2] + 0.34))
    bpy.context.object.data.materials.append(mat('band', '#3a3330', 0.6))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.025, location=(PIVOT[0] + L, PIVOT[1] - 0.6, PIVOT[2] - 0.34))
    bpy.context.object.data.materials.append(mat('band', '#3a3330', 0.6))
    return L

def build_bg():
    sc = reset(False)
    # sky gradient
    w = sc.world; nt = w.node_tree
    bg = nt.nodes['Background']; bg.inputs[1].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Window'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs[1], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (*srgb('#40538a'), 1); ramp.color_ramp.elements[1].color = (*srgb('#182042'), 1)
    nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    # backdrop plane so the sky shows (camera sees world through film); moon
    moon = mat('moon', '#fbe7b0', 0.9, 0.0, emit=('#fbe7b0', 0.85))
    sphere((1.2, 10, 3.95), (0.62, 0.05, 0.62), moon, 64)
    for s in (-1, 1):  # sleepy moon face
        bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.016, location=(1.2 + s * 0.17, 9.9, 4.0), rotation=(math.radians(90), 0, 0))
        t = bpy.context.object; t.data.materials.append(mat('moonface', '#7a5440', 1.0, emit=('#7a5440', 0.2)))
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
        for v in t.data.vertices: v.select = v.co.y > 0.0
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
        sphere((1.2 + s * 0.29, 9.9, 3.86), (0.07, 0.02, 0.045), mat('moonpink', '#f6b8a8', 1.0, emit=('#f6b8a8', 0.5)), 16)
    # distant hills
    hill = noise_mat('hillfar', '#2b3a63', '#33456f', 2, 0.95, 0.2)
    for (hx, hr, hz) in ((-3, 4, -3.2), (3.2, 4.5, -3.4)):
        sphere((hx, 12, hz), (hr, 0.5, 4.1), hill, 64)
    # ground: red felt (毛氈) on a wooden deck
    deck = wood('deck', '#6e4a36', '#7f5640')
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2.5, -0.01)); p = bpy.context.object; p.scale = (12, 14, 1); p.data.materials.append(deck)
    field = noise_mat('field', '#22345a', '#2c4068', 3, 0.95, 0.3)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, -0.05)); p2 = bpy.context.object; p2.scale = (14, 8, 1); p2.data.materials.append(field)
    felt = noise_mat('felt', '#b8463e', '#c75249', 60, 0.95, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.6, 0.0)); f = bpy.context.object; f.scale = (5.0, 3.2, 0.04); f.data.materials.append(felt)
    bevel(f, 0.01, 2)
    # susuki grass (pampas) on both sides
    stem = mat('susuki', '#b9a46a', 0.9); plume = noise_mat('plume', '#e7dcc0', '#f5eedc', 40, 0.95, 0.6)
    random.seed(3)
    for side in (-1, 1):
        for k in range(9):
            x = side * (2.35 + random.random() * 0.8); y = 1.6 + random.random() * 1.5
            h = 2.2 + random.random() * 1.8; lean = side * (0.08 + random.random() * 0.2)
            o = cyl((x + math.sin(lean) * h / 2, y, h / 2), 0.025, h, stem, 8, (0, lean, 0))
            p = sphere((x + math.sin(lean) * h, y, h + 0.1), (0.13, 0.13, 0.55), plume, 16, (0, lean + side * 0.4, 0))
    # tsukimi dango tower on a stand (sanbo) at the left back
    stand = wood('sanbo', '#d9b787', '#e8c99a')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.0, 2.4, 0.35)); s = bpy.context.object; s.scale = (0.8, 0.8, 0.7); s.data.materials.append(stand); bevel(s, 0.04)
    dango = mat('dango', '#fbf7ee', 0.85, sss=0.2)
    for lvl, n in enumerate((3, 2, 1)):
        for i in range(n):
            for j in range(n):
                sphere((-2.0 + (i - (n - 1) / 2) * 0.24, 2.4 + (j - (n - 1) / 2) * 0.24, 0.82 + lvl * 0.2), (0.13, 0.13, 0.12), dango, 24)
    # paper lantern (andon) at right back, glowing
    paper = mat('andon', '#fff0d0', 0.9, emit=('#ffc777', 2.5))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.1, 2.6, 0.9)); a = bpy.context.object; a.scale = (0.5, 0.5, 1.1); a.data.materials.append(paper); bevel(a, 0.03)
    frame = mat('andonframe', '#3a2a22', 0.8)
    for dz in (0.35, 1.45):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(2.1, 2.6, dz)); fr = bpy.context.object; fr.scale = (0.56, 0.56, 0.06); fr.data.materials.append(frame)
    bpy.ops.object.light_add(type='POINT', location=(2.1, 2.2, 1.0)); l = bpy.context.object; l.data.energy = 120; l.data.color = srgb('#ffbb66')
    # stars
    st = mat('star', '#ffffff', 1.0, emit=('#fff6e0', 3.0))
    random.seed(9)
    for i in range(70):
        sphere((random.uniform(-3, 3), 12, random.uniform(2.2, 8.5)), (0.018, 0.01, 0.018), st, 8)
    render(sc, 'bg')

def only(fn, name):
    sc = reset(); fn(); render(sc, name)

def build_plate():
    """Result art: a round mochi (with face) on a small wooden stand with a leaf."""
    sc = reset()
    stand = wood('sanbo', '#d9b787', '#e8c99a')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.3)); s = bpy.context.object; s.scale = (2.0, 1.4, 0.6); s.data.materials.append(stand); bevel(s, 0.05)
    m = mat('mochiF', '#fbf8f1', 0.55, 0.1, sss=0.3)
    sphere((0, 0.3, 1.05), (0.95, 0.85, 0.48), m, 64)
    sphere((0, 0.3, 1.72), (0.68, 0.6, 0.34), m, 64)
    mik = noise_mat('mikan', '#f08a2c', '#f6a24a', 30, 0.6, 0.5)
    sphere((0, 0.3, 2.22), (0.3, 0.3, 0.26), mik, 48)
    leaf = mat('leaf', '#5f9a52', 0.8)
    sphere((0.2, 0.3, 2.46), (0.16, 0.06, 0.03), leaf, 16, (0, math.radians(-20), 0))
    face(0, -0.47, 1.1, 1.6)
    render(sc, 'plate')

def scene_usu(): build_usu()
JOBS = {
    'bg': build_bg,
    'usu': lambda: only(build_usu, 'usu'),
    'mochi': lambda: [only(lambda s=s: build_mochi(s), 'mochi%d' % s) for s in range(3)],
    'usagi': lambda: only(lambda: rabbit(-1.78, '#fbf8f2', 22, 'hold', 'usagi'), 'usagi'),
    'kine': lambda: only(build_kine, 'kine'),
    'turner': lambda: [only(lambda p=p: rabbit(1.8, '#e8cfae', -22, p, 'turner'), 'turner_' + p) for p in ('idle', 'reach', 'ouch')],
    'plate': build_plate,
}
for k in (JOBS.keys() if WHAT == 'all' else WHAT.split(',')):
    JOBS[k]()
meta = {'pivot': proj(*[PIVOT[0], PIVOT[1] - 0.6, PIVOT[2]]), 'mochi': proj(USU[0], USU[1], MOCHI_Z), 'mochiTop': proj(USU[0], USU[1] - 0.3, MOCHI_Z + 0.3), 'pxu': PXU, 'kineLen': 1.27}
json.dump(meta, open(os.path.join(OUT, 'scene.json'), 'w'))
