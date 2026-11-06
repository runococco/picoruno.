# Renders the food pieces, bento boxes, lids and the table for bento.html.
# python3 render.py <what> <outdir>      what = all | pieces | <piece id> | boxes | table
# (needs `pip install bpy`). One grid cell = 1 Blender unit, camera looks straight down.
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
PX = 160            # pixels per grid cell
SAMPLES = int(os.environ.get('SAMPLES', '64'))
os.makedirs(OUT, exist_ok=True)

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def reset(transparent=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    w = bpy.data.worlds.new('w'); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.88, 0.84, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.65
    # soft key light from the upper left (top of the screen = +Y), plus a broad fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(30)
    s.rotation_euler = Euler((math.radians(-28), math.radians(-22), 0))
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 8))
    a = bpy.context.object; a.data.energy = 260; a.data.size = 10
    return sc

def mat(name, color, rough=0.7, spec=0.18, sss=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Coat Weight'].default_value = coat
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (0.4, 0.25, 0.12)
        b.inputs['Subsurface Scale'].default_value = 0.05
    return m

def noise_mat(name, c1, c2, scale=6, rough=0.75, bump=0.4, lo=0.35, hi=0.7, detail=6, spec=0.18, coord='Object'):
    """Principled with a two-colour noise ramp + matching bump."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = detail; nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs[coord], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    return m

def shade_smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def sub(o, lv=2):
    m = o.modifiers.new('s', 'SUBSURF'); m.levels = lv; m.render_levels = lv

def sphere(loc, scale, m, seg=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = scale; o.rotation_euler = rot
    shade_smooth(o); o.data.materials.append(m)
    return o

def rbox(loc, size, m, bevel=0.1, seg=5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bv = o.modifiers.new('b', 'BEVEL'); bv.width = bevel; bv.segments = seg; bv.limit_method = 'NONE'
    shade_smooth(o); o.data.materials.append(m)
    return o

def cyl(loc, r, depth, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; shade_smooth(o); o.data.materials.append(m)
    return o

def displace(o, strength=0.05, size=0.3, kind='CLOUDS', sub_lv=3):
    if sub_lv: sub(o, sub_lv)
    t = bpy.data.textures.new('t' + o.name, kind); t.noise_scale = size
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = strength; d.texture_coords = 'GLOBAL'
    return o

def face(x, y, z, s=1.0, cheeks=True, gap=0.11):
    """Two plain round black dot eyes (no highlight) + optional matte pink cheeks, facing the top camera."""
    blk = bpy.data.materials.get('eye') or mat('eye', (0.015, 0.012, 0.01), 1.0, 0.0)
    pnk = bpy.data.materials.get('cheek') or mat('cheek', '#f2a0a0', 1.0, 0.0)
    for sx in (-1, 1):
        sphere((x + sx * gap * s, y, z), (0.034 * s, 0.034 * s, 0.018), blk, 24)
        if cheeks:
            sphere((x + sx * gap * 1.75 * s, y - 0.06 * s, z - 0.006), (0.05 * s, 0.032 * s, 0.01), pnk, 24)

def cam(sc, w, h, px=PX, margin=0.0):
    bpy.ops.object.camera_add(location=(0, 0, 30))
    c = bpy.context.object; c.data.type = 'ORTHO'
    c.data.ortho_scale = max(w, h) + margin * 2
    c.data.clip_end = 100
    sc.camera = c
    sc.render.resolution_x = int(round((w + margin * 2) * px))
    sc.render.resolution_y = int(round((h + margin * 2) * px))
    return c

def render(sc, name):
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)

# ------------------------------------------------------------------ pieces
# every builder centres the food on the origin of its own footprint (w x h cells, h along +Y)

def p_tomato():
    red = mat('tomato', '#e0473a', 0.42, 0.22, sss=0.15)
    t = sphere((0, -0.02, 0.3), (0.4, 0.4, 0.34), red, 48)
    grn = mat('calyx', '#4f8a3a', 0.8)
    for i in range(5):
        a = i * math.tau / 5 + 0.3
        l = sphere((math.cos(a) * 0.1, -0.02 + math.sin(a) * 0.1, 0.64), (0.11, 0.035, 0.015), grn, 16, (0, 0, a))
    cyl((0, -0.02, 0.67), 0.025, 0.07, grn)
    face(0, -0.2, 0.6, 0.9)
    return 1, 1

def p_broccoli():
    stem = mat('stem', '#9cbf6a', 0.7)
    cyl((0, -0.25, 0.15), 0.1, 0.4, stem, (math.radians(70), 0, 0))
    fl = noise_mat('floret', '#3f7a33', '#6aa24c', 40, 0.9, 1.2, 0.4, 0.65)
    random.seed(3)
    for i in range(22):
        a = random.random() * math.tau; r = random.random() ** 0.6 * 0.3
        z = 0.32 + (0.3 - r) * 0.5
        s = 0.16 + random.random() * 0.05
        o = sphere((math.cos(a) * r, 0.05 + math.sin(a) * r, z), (s, s, s * 0.9), fl, 24)
        displace(o, 0.035, 0.05, sub_lv=2)
    return 1, 1

def p_karaage(loc=(0, 0), seed=1, s=1.0, face_on=True):
    m = bpy.data.materials.get('karaage') or noise_mat('karaage', '#9c5520', '#d9953f', 9, 0.8, 0.9, 0.3, 0.75, 8)
    o = sphere((loc[0], loc[1], 0.24 * s), (0.4 * s, 0.37 * s, 0.25 * s), m, 32, (0, 0, seed))
    displace(o, 0.12 * s, 0.22, sub_lv=3)
    o.modifiers['d'].texture.noise_scale = 0.2 + seed * 0.013
    o.modifiers['d'].texture_coords = 'OBJECT'
    if face_on: face(loc[0], loc[1] - 0.12 * s, 0.53 * s, 0.85 * s)
    return 1, 1

def p_sausage_octo():
    red = mat('octo', '#d9453f', 0.55, 0.2)
    inner = mat('octo_in', '#f1c0a2', 0.7)
    sphere((0, 0.0, 0.3), (0.31, 0.31, 0.3), red, 48)
    for i in range(8):
        a = i * math.tau / 8 + math.pi / 8
        sphere((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.09), (0.15, 0.09, 0.08), red, 24, (0, 0, a))
        sphere((math.cos(a) * 0.4, math.sin(a) * 0.4, 0.1), (0.06, 0.06, 0.06), inner, 16, (0, 0, a))
    face(0, -0.08, 0.59, 1.0)
    return 1, 1

def p_tamagoyaki():
    egg = noise_mat('egg', '#f2c64a', '#f7d872', 5, 0.75, 0.15, 0.3, 0.7, 4)
    edge = mat('eggedge', '#d9a239', 0.8)
    ring = mat('eggring', '#e0ab3c', 0.8)
    for k, y in enumerate((-0.5, 0.5)):
        rbox((0, y, 0.18), (0.88, 0.9, 0.36), edge, 0.16)
        rbox((0, y, 0.19), (0.8, 0.82, 0.36), egg, 0.14)
        # the rolled layers: thin flat loops on the cut face
        for i, f in enumerate((0.62, 0.38, 0.16)):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.32 * f / 0.62, minor_radius=0.012, location=(0.02 * i, y, 0.372))
            t = bpy.context.object; t.scale = (1.15, 0.85, 0.3); t.data.materials.append(ring); shade_smooth(t)
    face(0, -0.62, 0.38, 0.85)
    return 1, 2

def p_salmon():
    flesh = mat('salmon', '#f08a5d', 0.6, 0.2, sss=0.1)
    fat = mat('fat', '#fbd2b5', 0.7)
    skin = noise_mat('skin', '#6f6a66', '#b8b2a8', 30, 0.5, 0.3, 0.35, 0.65)
    grill = mat('grill', '#a2482a', 0.85)
    base = rbox((0, 0, 0.16), (0.86, 1.8, 0.3), flesh, 0.14)
    rbox((0.36, 0, 0.15), (0.16, 1.8, 0.28), skin, 0.08)
    for i in range(6):
        y = -0.75 + i * 0.3
        o = rbox((-0.05, y, 0.312), (0.34, 0.03, 0.02), fat, 0.01, 2)
        o.rotation_euler = (0, 0, math.radians(-18))
    for (x, y) in ((-0.2, -0.55), (0.1, 0.35), (-0.15, 0.7)):
        sphere((x, y, 0.315), (0.09, 0.05, 0.01), grill, 16, (0, 0, 0.5))
    face(-0.05, -0.2, 0.33, 0.9)
    return 1, 2

def p_wiener():
    red = mat('wiener', '#c9573f', 0.55, 0.2)
    cut = mat('wcut', '#e9a688', 0.7)
    for x in (-0.22, 0.22):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.19, depth=1.4, location=(x, 0, 0.2), rotation=(math.radians(90), 0, 0))
        o = bpy.context.object; o.data.materials.append(red)
        bv = o.modifiers.new('b', 'BEVEL'); bv.width = 0.17; bv.segments = 8; bv.limit_method = 'NONE'; shade_smooth(o)
        for i in range(4):
            g = rbox((x, -0.45 + i * 0.3, 0.385), (0.12, 0.045, 0.03), cut, 0.012, 2)
            g.rotation_euler = (0, 0, math.radians(25))
    face(-0.22, -0.18, 0.4, 0.75, cheeks=False, gap=0.08)
    face(0.22, -0.18, 0.4, 0.75, cheeks=False, gap=0.08)
    return 1, 2

def p_ebi():
    crumb = noise_mat('panko', '#c8802d', '#efc06a', 26, 0.9, 1.4, 0.3, 0.7, 10)
    tail = mat('tail', '#e2553a', 0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, -0.15, 0.22))
    b = bpy.context.object; b.scale = (0.3, 1.25, 0.22); b.data.materials.append(crumb); shade_smooth(b)
    bpy.ops.object.transform_apply(scale=True)
    for v in b.data.vertices:   # taper towards the tail (+Y) and bend slightly
        t = min(max((v.co.y + 1.25) / 2.5, 0.0), 1.0)
        k = 1 - 0.55 * t ** 1.6
        v.co.x *= k; v.co.z = (v.co.z) * (1 - 0.35 * t)
        v.co.x += 0.12 * math.sin(t * math.pi)
    displace(b, 0.04, 0.04, sub_lv=2)
    b.modifiers['d'].texture_coords = 'OBJECT'
    for s in (-1, 1):
        sphere((s * 0.11, 1.18, 0.16), (0.12, 0.2, 0.04), tail, 24, (0, 0, -s * 0.35))
    sphere((0, 1.12, 0.17), (0.06, 0.1, 0.05), tail, 16)
    face(0.0, -0.95, 0.45, 0.85)
    return 1, 3

def p_hamburg():
    meat = noise_mat('meat', '#5c3420', '#7d4a2b', 14, 0.8, 0.8, 0.3, 0.7)
    sauce = mat('sauce', '#4a1f12', 0.38, 0.25)
    o = sphere((0, 0, 0.2), (0.9, 0.84, 0.26), meat, 64)
    displace(o, 0.03, 0.15, sub_lv=2)
    s = sphere((0, 0.08, 0.33), (0.66, 0.52, 0.15), sauce, 64)
    displace(s, 0.04, 0.4, sub_lv=2)
    pars = mat('parsley', '#3f7a33', 0.9)
    random.seed(5)
    for i in range(14):
        sphere((random.uniform(-0.3, 0.35), random.uniform(0.0, 0.4), 0.46), (0.025, 0.02, 0.008), pars, 8, (0, 0, random.random() * 3))
    car = mat('carrot', '#ec8a2e', 0.6)
    face(0, -0.5, 0.42, 1.25)
    return 2, 2

def rice_block(w, h):
    rice = mat('rice', '#f7f4ec', 0.75, 0.15, sss=0.25)
    rbox((0, 0, 0.13), (w - 0.08, h - 0.08, 0.26), rice, 0.12)
    # grains: emit a particle system of small ellipsoids from a plane at the top surface
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=(50, 0, 0))
    g = bpy.context.object; g.scale = (0.065, 0.034, 0.03); g.data.materials.append(rice); shade_smooth(g)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.27))
    p = bpy.context.object; p.scale = (w - 0.16, h - 0.16, 1)
    bpy.ops.object.transform_apply(scale=True)
    ps = p.modifiers.new('ps', 'PARTICLE_SYSTEM').particle_system
    st = ps.settings
    st.count = int(650 * w * h); st.frame_start = st.frame_end = 1; st.lifetime = 1000
    st.emit_from = 'FACE'; st.distribution = 'RAND'; st.use_emit_random = True
    st.physics_type = 'NO'; st.render_type = 'OBJECT'; st.instance_object = g
    st.particle_size = 1.0; st.size_random = 0.3
    st.use_rotations = True; st.rotation_mode = 'NONE'; st.phase_factor_random = 2.0; st.rotation_factor_random = 1.0
    st.normal_factor = 0.0
    p.show_instancer_for_render = False
    sesame = mat('goma', '#2a221c', 0.8)
    random.seed(w * 10 + h)
    for i in range(int(10 * w * h)):
        sphere((random.uniform(-w / 2 + 0.15, w / 2 - 0.15), random.uniform(-h / 2 + 0.15, h / 2 - 0.15), 0.3),
               (0.022, 0.012, 0.01), sesame, 8, (0, 0, random.random() * 3))

def p_rice22():
    rice_block(2, 2)
    ume = noise_mat('ume', '#b8323a', '#d84b4f', 10, 0.55, 0.6, 0.35, 0.7)
    o = sphere((0, 0.05, 0.36), (0.26, 0.24, 0.16), ume, 32)
    displace(o, 0.02, 0.1, sub_lv=2)
    face(0, -0.03, 0.51, 0.75)
    return 2, 2

def p_rice23():
    rice_block(2, 3)
    nori = noise_mat('nori', '#1f2a1d', '#33402c', 30, 0.7, 0.5, 0.3, 0.7)
    for y in (-0.7, 0.0, 0.7):
        o = rbox((0.0, y, 0.29), (1.1, 0.34, 0.012), nori, 0.03, 2)
    ume = noise_mat('ume', '#b8323a', '#d84b4f', 10, 0.55, 0.6, 0.35, 0.7)
    o = sphere((0, 1.08, 0.35), (0.2, 0.18, 0.13), ume, 32)
    face(0, 1.02, 0.47, 0.6, cheeks=False, gap=0.09)
    return 2, 3

def p_karaage3():
    # three karaage on a lettuce frill in an L (cells (0,0) (0,1) (1,1) with y up = rows bottom->top)
    lettuce = noise_mat('lettuce', '#7fb34e', '#b9d97a', 5, 0.8, 0.8, 0.3, 0.75)
    for (x, y) in ((-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5)):
        o = sphere((x, y, 0.05), (0.5, 0.5, 0.05), lettuce, 32)
        displace(o, 0.12, 0.12, sub_lv=3)
    for i, (x, y) in enumerate(((-0.5, 0.5), (-0.5, -0.5), (0.5, -0.5))):
        p_karaage((x, y), seed=i + 2, s=0.95, face_on=(i == 1))
    return 2, 2

def p_potesara():
    cup = mat('cup', '#7fc3c0', 0.6)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.38, radius2=0.46, depth=0.32, location=(0, 0, 0.16))
    o = bpy.context.object; o.data.materials.append(cup)
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.02
    for v in o.data.vertices:  # pleated rim
        a = math.atan2(v.co.y, v.co.x); k = 1 + 0.06 * math.cos(a * 12)
        v.co.x *= k; v.co.y *= k
    pot = noise_mat('potato', '#efe1b0', '#fbf3d2', 8, 0.85, 0.9, 0.3, 0.7)
    p = sphere((0, 0, 0.3), (0.4, 0.4, 0.22), pot, 48)
    displace(p, 0.05, 0.12, sub_lv=2)
    gr = mat('cucumber', '#8bbd5a', 0.7)
    car = mat('carrot', '#ec8a2e', 0.7)
    random.seed(8)
    for i in range(7):
        a = random.random() * math.tau; r = random.uniform(0.05, 0.27)
        sphere((math.cos(a) * r, math.sin(a) * r, 0.47), (0.05, 0.035, 0.012), gr if i % 2 else car, 12, (0, 0, a))
    face(0, -0.08, 0.52, 0.85)
    return 1, 1

PIECES = {
    'tomato': p_tomato, 'broccoli': p_broccoli, 'karaage': p_karaage, 'octo': p_sausage_octo,
    'potesara': p_potesara, 'tamago': p_tamagoyaki, 'salmon': p_salmon, 'wiener': p_wiener,
    'ebi': p_ebi, 'hamburg': p_hamburg, 'rice22': p_rice22, 'rice23': p_rice23, 'karaage3': p_karaage3,
}

def render_piece(name):
    sc = reset()
    w, h = PIECES[name]()
    cam(sc, w, h, margin=0.06)
    render(sc, f'p_{name}.png')

# ------------------------------------------------------------------ box, lid, table

def wood_mat(name, c1, c2, scale=1.5, rough=0.65):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 14, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    nz.inputs['Distortion'].default_value = 2.5
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = 2.2; wv.inputs['Distortion'].default_value = 2.5; wv.inputs['Detail'].default_value = 2
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.35
    nt.links.new(nz.outputs['Fac'], mix.inputs[2]); nt.links.new(wv.outputs['Fac'], mix.inputs[3])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = 0.3; r.color_ramp.elements[1].position = 0.75
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(mix.outputs[0], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15
    nt.links.new(mix.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = 0.2
    return m

WALL = 0.32   # wall thickness in cells (shared with the game: box image = (W + 2*WALL) x (H + 2*WALL))

def box(W, H):
    sc = reset()
    outer = wood_mat('cedar', '#cf9a62', '#e3b47e')
    inner = wood_mat('cedar_in', '#e6bf8f', '#efcfa3', 2.0, 0.8)
    ow, oh = W + 2 * WALL, H + 2 * WALL
    o = rbox((0, 0, 0.25), (ow, oh, 0.5), outer, 0.28, 8)
    # carve the inside with a boolean (rounded inner corners)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.6))
    cut = bpy.context.object; cut.scale = (W + 0.02, H + 0.02, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    cb = cut.modifiers.new('b', 'BEVEL'); cb.width = 0.12; cb.segments = 6; cb.limit_method = 'NONE'
    bo = o.modifiers.new('bool', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
    cut.hide_render = True
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.11))
    fl = bpy.context.object; fl.scale = (W + 0.05, H + 0.05, 1); fl.data.materials.append(inner)
    # cherry-bark band (magewappa stitch) on the left wall
    bark = noise_mat('bark', '#5a3824', '#7a4e33', 30, 0.8, 0.5)
    rbox((-ow / 2 + WALL / 2, 0, 0.51), (0.12, 0.62, 0.02), bark, 0.02, 2)
    cam(sc, ow, oh, margin=0.0)
    render(sc, f'box{W}x{H}.png')

def lid(W, H):
    sc = reset()
    ow, oh = W + 2 * WALL, H + 2 * WALL
    top = wood_mat('cedar', '#cf9a62', '#e3b47e')
    rbox((0, 0, 0.2), (ow + 0.04, oh + 0.04, 0.4), top, 0.3, 8)
    band = noise_mat('band', '#c94f45', '#d8625a', 60, 0.95, 0.3, 0.3, 0.7)
    # a cloth band (furoshiki-like ribbon) tied across the lid with a small knot
    rbox((0, 0, 0.405), (0.42, oh + 0.06, 0.04), band, 0.05, 3)
    k = sphere((0, 0, 0.47), (0.26, 0.2, 0.1), band, 32)
    for s in (-1, 1):
        sphere((s * 0.3, 0.05, 0.44), (0.24, 0.13, 0.06), band, 24, (0, 0, s * 0.4))
    cam(sc, ow + 0.04, oh + 0.04, margin=0.0)
    render(sc, f'lid{W}x{H}.png')

def table():
    """Background: gingham cloth on a wooden table, 9:16."""
    sc = reset(False)
    sc.cycles.samples = max(SAMPLES, 64)
    m = bpy.data.materials.new('gingham'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    def stripe(axis):
        mth = nt.nodes.new('ShaderNodeMath'); mth.operation = 'MULTIPLY'; mth.inputs[1].default_value = 1.2
        nt.links.new(sep.outputs[axis], mth.inputs[0])
        fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; nt.links.new(mth.outputs[0], fr.inputs[0])
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], lt.inputs[0]); return lt
    sx, sy = stripe(0), stripe(1)
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    nt.links.new(sx.outputs[0], add.inputs[0]); nt.links.new(sy.outputs[0], add.inputs[1])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = 'CONSTANT'
    e = r.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*srgb('#f6efe4'), 1)
    e[1].position = 0.45; e[1].color = (*srgb('#e9b9a8'), 1)
    e3 = e.new(0.9); e3.color = (*srgb('#d98f7c'), 1)
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.5
    nt.links.new(add.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], r.inputs['Fac'])
    # weave: fine noise darkening + bump
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 220; nz.inputs['Detail'].default_value = 2
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.12
    nt.links.new(r.outputs['Color'], mx.inputs[6]); nt.links.new(nz.outputs['Fac'], mx.inputs[7])
    nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.95; b.inputs['Specular IOR Level'].default_value = 0.1
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    cl = bpy.context.object; cl.scale = (12, 20, 1); bpy.ops.object.transform_apply(scale=True); cl.data.materials.append(m)
    sub(cl, 0)
    # gentle folds
    bpy.ops.object.modifier_add(type='SUBSURF'); cl.modifiers[-1].subdivision_type = 'SIMPLE'; cl.modifiers[-1].levels = cl.modifiers[-1].render_levels = 6
    t = bpy.data.textures.new('fold', 'CLOUDS'); t.noise_scale = 2.2
    d = cl.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = 0.12
    W, H = 9.0, 16.0
    bpy.ops.object.camera_add(location=(0, 0, 30)); c = bpy.context.object
    c.data.type = 'ORTHO'; c.data.ortho_scale = H; sc.camera = c; c.data.clip_end = 100
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280
    render(sc, 'table.png')

def chopsticks():
    sc = reset()
    w = wood_mat('hashi', '#7a4a2c', '#9a6440', 2, 0.6)
    tip = mat('hashitip', '#e9d8b8', 0.7)
    for x in (-0.1, 0.1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius1=0.05, radius2=0.025, depth=4.4, location=(x, 0, 0.1), rotation=(math.radians(90), 0, 0)) if False else None
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.055, radius2=0.025, depth=4.4, location=(x, 0, 0.1), rotation=(math.radians(-90), 0, 0))
        o = bpy.context.object; o.data.materials.append(w)
    rest = mat('rest', '#8fb6c9', 0.6)
    o = sphere((0, -1.4, 0.06), (0.32, 0.12, 0.08), rest, 32)
    cam(sc, 0.6, 4.6, px=80)
    render(sc, 'hashi.png')

SIZES = [(3, 3), (4, 3), (4, 4), (5, 4), (5, 5)]

if WHAT in ('all', 'pieces'):
    for n in PIECES: render_piece(n)
elif WHAT in PIECES:
    render_piece(WHAT)
if WHAT in ('all', 'boxes'):
    for (w, h) in SIZES: box(w, h); lid(w, h)
if WHAT.startswith('box') and 'x' in WHAT:
    w, h = map(int, WHAT[3:].split('x')); box(w, h); lid(w, h)
if WHAT in ('all', 'table'): table()
if WHAT in ('all', 'hashi'): chopsticks()
