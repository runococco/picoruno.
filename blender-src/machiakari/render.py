# Renders the houses (lit / asleep), trees and the floating island for machiakari.html.
# python3 render.py <what> <outdir>     what = all | houses | <house id> | island | trees
# Camera: orthographic, looking along +Y, tilted down by ELEV degrees. Ground plane z=0.
# Screen mapping used by the game (unit = 1 Blender unit):
#   sx = X * PX,   sy = (-Y * sin(ELEV) - Z * cos(ELEV)) * PX   (relative to the sprite anchor)
import bpy, math, sys, os, random
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
ELEV = 38.0
PX = 150                      # pixels per unit
os.makedirs(OUT, exist_ok=True)

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#3c4a7a'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    # moonlight from upper left behind the viewer, cool
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 1.6; s.data.angle = math.radians(12)
    s.data.color = srgb('#c9d6ff')
    s.rotation_euler = Euler((math.radians(50), 0, math.radians(-35)))
    # soft rim from behind (blue)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    r = bpy.context.object; r.data.energy = 0.8; r.data.color = srgb('#8fa6ff')
    r.rotation_euler = Euler((math.radians(-55), 0, math.radians(20)))
    return sc

def mat(name, color, rough=0.75, spec=0.15, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(emit[0]), 1)
        b.inputs['Emission Strength'].default_value = emit[1]
    return m

def noise_mat(name, c1, c2, scale=6, rough=0.8, bump=0.3):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 5
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = .35; r.color_ramp.elements[1].position = .7
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .12
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(loc, size, m, bevel=0.03, seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    smooth(o); o.data.materials.append(m); return o

def sphere(loc, scale, m, seg=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = scale; o.rotation_euler = rot; smooth(o); o.data.materials.append(m); return o

def cyl(loc, r, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; smooth(o); o.data.materials.append(m); return o

def cone(loc, r1, r2, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; smooth(o) if verts > 8 else None; o.data.materials.append(m); return o

def gable(cx, cy, z, w, d, h, m, over=0.06):
    """Gable roof: ridge along X. w = width (x), d = depth (y)."""
    import bmesh
    me = bpy.data.meshes.new('roof'); o = bpy.data.objects.new('roof', me); bpy.context.collection.objects.link(o)
    bm = bmesh.new()
    W, D = w / 2 + over, d / 2 + over
    v = [bm.verts.new(p) for p in [(-W, -D, 0), (W, -D, 0), (W, D, 0), (-W, D, 0), (-W, 0, h), (W, 0, h)]]
    bm.faces.new([v[0], v[1], v[5], v[4]]); bm.faces.new([v[3], v[4], v[5], v[2]])
    bm.faces.new([v[0], v[4], v[3]]); bm.faces.new([v[1], v[2], v[5]]); bm.faces.new([v[0], v[3], v[2], v[1]])
    bm.to_mesh(me); bm.free()
    o.location = (cx, cy, z)
    s = o.modifiers.new('s', 'SOLIDIFY'); s.thickness = 0.05
    b = o.modifiers.new('b', 'BEVEL'); b.width = 0.015; b.segments = 2; b.limit_method = 'NONE'
    o.data.materials.append(m); return o

def window(x, y, z, w, h, lit, round_=False):
    frame = mat('frame', '#5a3a2c', 0.8)
    glass = mat('win_on', '#ffd27a', 0.5, 0.1, emit=('#ffc860', 7.0)) if lit else mat('win_off', '#2b3354', 0.35, 0.3)
    if round_:
        cyl((x, y - 0.005, z), w / 2 + 0.025, 0.02, frame, 32, (math.radians(90), 0, 0))
        cyl((x, y - 0.012, z), w / 2, 0.02, glass, 32, (math.radians(90), 0, 0))
    else:
        box((x, y - 0.005, z), (w + 0.05, 0.02, h + 0.05), frame, 0.008, 2)
        box((x, y - 0.012, z), (w, 0.02, h), glass, 0.0)
        box((x, y - 0.024, z), (w, 0.01, 0.018), frame, 0.0)  # mullion
        box((x, y - 0.024, z), (0.018, 0.01, h), frame, 0.0)

def door(x, y, z0, w, h, color):
    m = mat('door_' + color, color, 0.7)
    box((x, y - 0.005, z0 + h / 2), (w, 0.03, h), m, 0.02, 3)
    sphere((x + w * 0.3, y - 0.03, z0 + h * 0.45), (0.018, 0.018, 0.018), mat('knob', '#d9b45a', 0.5))

def face(x, y, z, lit, s=1.0):
    """Front-facing face on a wall at plane y (wall normal -Y). Lit = awake round eyes, else sleeping closed eyes."""
    blk = mat('eye', (0.02, 0.015, 0.012), 1.0, 0.0)
    pnk = mat('cheek', '#f2a0a0', 1.0, 0.0)
    for sx in (-1, 1):
        if lit:
            sphere((x + sx * 0.075 * s, y - 0.005, z), (0.03 * s, 0.012, 0.03 * s), blk, 20)
        else:
            # closed eyes: a small downward arc made from a torus segment
            bpy.ops.mesh.primitive_torus_add(major_radius=0.026 * s, minor_radius=0.0065 * s, major_segments=24, minor_segments=8,
                                             location=(x + sx * 0.075 * s, y - 0.006, z + 0.008 * s), rotation=(math.radians(90), 0, 0))
            t = bpy.context.object; t.data.materials.append(blk)
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
            for v in t.data.vertices: v.select = v.co.y > 0.002 * s   # local +Y becomes world up: drop it -> a ∪ shaped arc
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
        sphere((x + sx * 0.13 * s, y - 0.004, z - 0.04 * s), (0.032 * s, 0.008, 0.019 * s), pnk, 16)

def glow_light(loc, energy=60, color='#ffbe6a', size=0.25):
    bpy.ops.object.light_add(type='POINT', location=loc)
    l = bpy.context.object; l.data.energy = energy; l.data.color = srgb(color); l.data.shadow_soft_size = size
    return l

# ---------------------------------------------------------------- houses
# each builder builds a house centred at the origin, front wall facing -Y (towards the camera)

def h_cottage(lit):
    wall = noise_mat('wall_cream', '#eadcc4', '#f4ead8', 9)
    roof = noise_mat('roof_red', '#b8584a', '#cf6c5a', 14)
    W, D, H = 0.86, 0.66, 0.56
    box((0, 0, H / 2), (W, D, H), wall, 0.03)
    gable(0, 0, H, W, D, 0.36, roof)
    box((0.24, 0.12, H + 0.3), (0.12, 0.12, 0.3), mat('brick', '#8a5a48', 0.8), 0.01)
    door(0, -D / 2, 0, 0.18, 0.3, '#6c8fb3')
    window(-0.27, -D / 2, 0.3, 0.16, 0.16, lit)
    window(0.27, -D / 2, 0.3, 0.16, 0.16, lit)
    face(0, -D / 2, 0.45, lit, 1.35)
    if lit: glow_light((0, -D / 2 - 0.35, 0.35), 25)

def h_tall(lit):
    wall = noise_mat('wall_mint', '#c6dccf', '#d9eade', 9)
    roof = noise_mat('roof_navy', '#4e5c86', '#5f6e99', 14)
    W, D, H = 0.6, 0.6, 1.0
    box((0, 0, H / 2), (W, D, H), wall, 0.03)
    gable(0, 0, H, W, D, 0.42, roof)
    door(0, -D / 2, 0, 0.17, 0.28, '#b36a5e')
    for z in (0.5, 0.78):
        window(-0.15, -D / 2, z, 0.13, 0.15, lit)
        window(0.15, -D / 2, z, 0.13, 0.15, lit)
    face(0, -D / 2, 0.36, lit, 1.2)
    if lit: glow_light((0, -D / 2 - 0.35, 0.5), 30)

def h_round(lit):
    wall = noise_mat('wall_butter', '#efdca4', '#f6e8bd', 9)
    roof = noise_mat('roof_mint', '#5f9c8c', '#74b09f', 14)
    cyl((0, 0, 0.3), 0.4, 0.6, wall, 48)
    cone((0, 0, 0.78), 0.48, 0.0, 0.42, roof, 48)
    sphere((0, 0, 1.0), (0.04, 0.04, 0.04), mat('knob', '#d9b45a', 0.5))
    door(0, -0.385, 0, 0.17, 0.3, '#7d5b8f')
    window(-0.25, -0.33, 0.36, 0.13, 0.13, lit, True)
    window(0.25, -0.33, 0.36, 0.13, 0.13, lit, True)
    face(0, -0.395, 0.47, lit, 1.3)
    if lit: glow_light((0, -0.75, 0.35), 25)

def h_shop(lit):
    wall = noise_mat('wall_pink', '#ecc5bb', '#f3d6ce', 9)
    W, D, H = 0.92, 0.62, 0.62
    box((0, 0, H / 2), (W, D, H), wall, 0.03)
    box((0, 0, H + 0.04), (W + 0.06, D + 0.06, 0.08), mat('cornice', '#f6efe3', 0.8), 0.02)
    # striped awning
    for i in range(8):
        m = mat('aw_r', '#c9584c', 0.85) if i % 2 == 0 else mat('aw_w', '#f6efe3', 0.85)
        o = box((-W / 2 + W / 16 + i * W / 8, -D / 2 - 0.1, 0.5), (W / 8, 0.22, 0.03), m, 0.0)
        o.rotation_euler = (math.radians(-28), 0, 0)
    box((0, -D / 2, 0.24), (0.6, 0.02, 0.3), mat('frame', '#5a3a2c', 0.8), 0.01)
    glass = mat('win_on', '#ffd27a', 0.5, 0.1, emit=('#ffc860', 7.0)) if lit else mat('win_off', '#2b3354', 0.35, 0.3)
    box((0, -D / 2 - 0.012, 0.24), (0.54, 0.02, 0.25), glass, 0.0)
    face(0, -D / 2, 0.565, lit, 1.25)
    if lit: glow_light((0, -D / 2 - 0.4, 0.3), 32)

def h_tower(lit):
    wall = noise_mat('wall_lav', '#d3cbe3', '#e1dbee', 9)
    roof = noise_mat('roof_red', '#b8584a', '#cf6c5a', 14)
    box((0, 0, 0.35), (0.62, 0.62, 0.7), wall, 0.03)
    box((0, 0, 0.88), (0.44, 0.44, 0.36), wall, 0.03)
    cone((0, 0, 1.24), 0.36, 0.0, 0.36, roof, 4, (0, 0, math.radians(45)))
    clock = mat('clock_on', '#fff3cf', 0.6, 0.1, emit=('#ffe7a8', 3.0)) if lit else mat('clock_off', '#c9c6d8', 0.6)
    cyl((0, -0.225, 0.9), 0.13, 0.02, clock, 40, (math.radians(90), 0, 0))
    hand = mat('frame', '#5a3a2c', 0.8)
    box((0, -0.24, 0.94), (0.016, 0.01, 0.09), hand, 0.0)
    box((0.03, -0.24, 0.9), (0.07, 0.01, 0.016), hand, 0.0)
    door(0, -0.31, 0, 0.18, 0.3, '#5f7f6d')
    window(-0.19, -0.31, 0.5, 0.1, 0.14, lit)
    window(0.19, -0.31, 0.5, 0.1, 0.14, lit)
    face(0, -0.31, 0.42, lit, 1.2)
    if lit: glow_light((0, -0.7, 0.5), 30)

HOUSES = {'cottage': h_cottage, 'tall': h_tall, 'round': h_round, 'shop': h_shop, 'tower': h_tower}

def cam(sc, w, h, cz):
    """Ortho camera framing a w x h (units) window centred at height cz above the origin."""
    el = math.radians(ELEV); d = 20
    tgt = Vector((0, 0, cz))
    loc = tgt + Vector((0, -math.cos(el) * d, math.sin(el) * d))
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = max(w, h); c.data.clip_end = 100
    sc.camera = c
    sc.render.resolution_x = int(w * PX); sc.render.resolution_y = int(h * PX)
    return c

SPR_W, SPR_H, SPR_CZ = 1.3, 1.6, 0.55     # house sprite window (units) and its centre height

def render(sc, name):
    sc.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True); print('wrote', name, flush=True)

def house(name):
    for lit in (False, True):
        sc = reset()
        HOUSES[name](lit)
        if lit:
            # lit houses: warmer world so the walls pick up the glow
            sc.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
        cam(sc, SPR_W, SPR_H, SPR_CZ)
        render(sc, f'h_{name}_{"on" if lit else "off"}.png')

def tree(kind, i):
    sc = reset()
    random.seed(i * 7 + 1)
    trunk = mat('trunk', '#6b4a3a', 0.8)
    if kind == 'pine':
        cyl((0, 0, 0.12), 0.06, 0.24, trunk, 16)
        g = noise_mat('pine', '#2f5a52', '#3f7266', 10)
        for k, (z, r) in enumerate(((0.3, 0.34), (0.55, 0.27), (0.78, 0.19))):
            cone((0, 0, z), r, 0.02, 0.36, g, 32)
    else:
        cyl((0, 0, 0.15), 0.06, 0.3, trunk, 16)
        g = noise_mat('leaf', '#3d6b4f', '#50835f', 8)
        for k in range(5):
            a = k / 5 * math.tau
            sphere((math.cos(a) * 0.14, math.sin(a) * 0.1, 0.45 + random.random() * 0.15), (0.2, 0.2, 0.18), g, 24)
        sphere((0, 0, 0.62), (0.22, 0.22, 0.2), g, 24)
    cam(sc, 1.0, 1.3, 0.45)
    render(sc, f't_{kind}{i}.png')

ISLAND_RX, ISLAND_RY = 3.3, 2.6
def island():
    sc = reset()
    grass = noise_mat('grass', '#3e6a58', '#4f7d66', 4, 0.9, 0.4)
    earth = noise_mat('earth', '#5b4a5f', '#6d586c', 6, 0.9, 0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1, depth=0.24, location=(0, 0, -0.12))
    top = bpy.context.object; top.scale = (ISLAND_RX, ISLAND_RY, 1); top.data.materials.append(grass)
    b = top.modifiers.new('b', 'BEVEL'); b.width = 0.08; b.segments = 4; b.limit_method = 'NONE'; smooth(top)
    # rocky underside: a squashed cone below
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1, radius2=0.18, depth=2.8, location=(0, 0, -1.62), rotation=(math.pi, 0, 0))
    bot = bpy.context.object; bot.scale = (ISLAND_RX * 0.97, ISLAND_RY * 0.97, 1); bot.rotation_euler = (math.pi, 0, 0)
    bot.data.materials.append(earth); smooth(bot)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    sub = bot.modifiers.new('s', 'SUBSURF'); sub.levels = sub.render_levels = 2
    t = bpy.data.textures.new('rock', 'CLOUDS'); t.noise_scale = 0.6
    d = bot.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = 0.35
    # little stones and flowers on the grass edge
    random.seed(4)
    st = mat('stone', '#8d8aa0', 0.8)
    for i in range(26):
        a = random.random() * math.tau; r = 0.86 + random.random() * 0.1
        sphere((math.cos(a) * ISLAND_RX * r, math.sin(a) * ISLAND_RY * r, 0.02), (0.08, 0.06, 0.04), st, 12, (0, 0, a))
    fl = [mat('fl1', '#f2d6a2', 0.8), mat('fl2', '#e9b2c0', 0.8), mat('fl3', '#cfd9f2', 0.8)]
    for i in range(70):
        a = random.random() * math.tau; r = random.random() ** 0.5 * 0.95
        sphere((math.cos(a) * ISLAND_RX * r, math.sin(a) * ISLAND_RY * r, 0.01), (0.025, 0.025, 0.015), fl[i % 3], 8)
    W = ISLAND_RX * 2 + 0.4
    el = math.radians(ELEV)
    top = ISLAND_RY * math.sin(el) + 0.25          # screen units above the island centre
    bot = 3.1 * math.cos(el) + 0.2                 # below (tip of the rock)
    H = top + bot
    # camera target height so the frame spans [-bot, top] around the island centre
    cz = (top - bot) / 2 / math.cos(el)
    cam(sc, W, H, cz)
    render(sc, 'island.png')
    with open(os.path.join(OUT, 'island.json'), 'w') as f:
        f.write('{"w":%f,"h":%f,"cz":%f}' % (W, H, cz))

if WHAT in ('all', 'houses'):
    for n in HOUSES: house(n)
elif WHAT in HOUSES:
    house(WHAT)
if WHAT in ('all', 'trees'):
    for i in range(2): tree('pine', i); tree('round', i)
if WHAT in ('all', 'island'):
    island()
