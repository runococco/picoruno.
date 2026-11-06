# Renders the art for hanabi.html: a summer-night garden seen from the veranda, wind chime, pig mosquito-coil holder.
import bpy, bmesh, math, sys, os, random, json
from mathutils import Vector, Euler

OUT = sys.argv[-1] if len(sys.argv) > 2 else 'out'
WHAT = sys.argv[-2] if len(sys.argv) > 2 else 'all'
SAMPLES = int(os.environ.get('SAMPLES', '64'))
PX = 120
os.makedirs(OUT, exist_ok=True)
META_PATH = os.path.join(OUT, 'meta.json')
META = json.load(open(META_PATH)) if os.path.exists(META_PATH) else {}

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*srgb('#cfe4f5'), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.75
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    s = bpy.context.object; s.data.energy = 3.4; s.data.angle = math.radians(20); s.data.color = srgb('#fff4e0')
    s.rotation_euler = Euler((math.radians(40), math.radians(-30), math.radians(-25)))
    return sc

def mat(name, color, rough=0.75, spec=0.15, sss=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Scale'].default_value = 0.1
    return m

def noise_mat(name, c1, c2, scale=6, rough=0.85, bump=0.3, lo=.35, hi=.7):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*srgb(c1), 1); r.color_ramp.elements[1].color = (*srgb(c2), 1)
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = .12
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def box(loc, size, m, bevel=0.03, seg=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.rotation_euler = rot
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'NONE'
    smooth(o); o.data.materials.append(m); return o

def sphere(loc, scale, m, seg=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = scale; o.rotation_euler = rot; smooth(o); o.data.materials.append(m); return o

def cyl_flat(loc, r, d, m, verts=64, bevel=.03):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc)
    o = bpy.context.object; b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    try: bpy.ops.object.shade_smooth_by_angle()
    except Exception: pass
    o.data.materials.append(m); return o

def cyl(loc, r, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; smooth(o); o.data.materials.append(m); return o

def cone(loc, r1, r2, d, m, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    if verts > 8: smooth(o)
    o.data.materials.append(m); return o

def displace(o, strength, size, lv=2):
    s = o.modifiers.new('s', 'SUBSURF'); s.levels = s.render_levels = lv
    t = bpy.data.textures.new('t' + o.name, 'CLOUDS'); t.noise_scale = size
    d = o.modifiers.new('d', 'DISPLACE'); d.texture = t; d.strength = strength; d.texture_coords = 'OBJECT'
    return o


def emis(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n_ in list(nt.nodes):
        if n_.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n_)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*srgb(color), 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs[0]); return m

def sky_mat():
    m = bpy.data.materials.new('sky'); m.use_nodes = True; nt = m.node_tree
    for n_ in list(nt.nodes):
        if n_.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n_)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sp.inputs[0])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = .0; r.color_ramp.elements[1].position = .55
    r.color_ramp.elements[0].color = (*srgb('#2a3a6a'), 1); r.color_ramp.elements[1].color = (*srgb('#0e1430'), 1)
    nt.links.new(sp.outputs['Z'] if False else sp.outputs['Y'], r.inputs['Fac'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[1].default_value = 1.0
    nt.links.new(r.outputs['Color'], e.inputs[0]); nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs[0]); return m

def pig(x, y, z, s=1.0, rotz=0.0):
    """Katori-buta: a round ceramic pig that holds the mosquito coil (open snout towards the camera)."""
    cer = mat('ceramic', '#f1ebdf', .35, .35); ink = mat('eye', (0.015, 0.012, 0.012), 1.0, 0.0); pink = mat('cheek', '#f2a0a0', 1, 0)
    rz = Euler((0, 0, rotz))
    def P(dx, dy, dz): v = rz.to_matrix() @ Vector((dx * s, dy * s, dz * s)); return (x + v.x, y + v.y, z + v.z)
    sphere(P(0, 0, .42), (.5 * s, .62 * s, .42 * s), cer, 48, rot=(0, 0, rotz))
    cyl(P(0, -.6, .42), .26 * s, .16 * s, cer, 32, rot=(math.radians(90), 0, rotz))
    cyl(P(0, -.69, .42), .19 * s, .02 * s, mat('hole', '#2a1c14', 1, 0), 32, rot=(math.radians(90), 0, rotz))
    for sx in (-1, 1):
        cone(P(sx * .26, -.32, .78), .11 * s, .0, .18 * s, cer, 16, rot=(math.radians(-30), sx * math.radians(20), rotz))
        sphere(P(sx * .2, -.5, .58), (.035 * s, .02 * s, .035 * s), ink, 16, rot=(0, 0, rotz))
        sphere(P(sx * .3, -.48, .45), (.05 * s, .015 * s, .03 * s), pink, 16, rot=(0, 0, rotz))
        for sy in (-1, 1): cyl(P(sx * .25, sy * .3, .06), .08 * s, .14 * s, cer, 16)

def bg():
    sc = reset(); sc.render.film_transparent = False
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    w = sc.world.node_tree.nodes['Background']; w.inputs[0].default_value = (*srgb('#1b2448'), 1); w.inputs[1].default_value = .35
    # moonlight from behind-left, warm room light from behind the camera
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10)); s = bpy.context.object; s.data.energy = 1.5; s.data.color = srgb('#b8c8ff')
    s.rotation_euler = Euler((math.radians(-55), math.radians(-30), 0)); s.data.angle = math.radians(8)
    bpy.ops.object.light_add(type='AREA', location=(0, -8, 3)); a = bpy.context.object; a.data.energy = 260; a.data.size = 5; a.data.color = srgb('#ffc98a')
    a.rotation_euler = Euler((math.radians(70), 0, 0))
    # ground, stones, fence, trees, sky
    soil = noise_mat('soil', '#2c2620', '#3c342a', scale=3, bump=.4, rough=.95)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=1, location=(0, 8, 0)); g = bpy.context.object; g.scale = (40, 40, 1)
    bpy.ops.object.transform_apply(scale=True); g.data.materials.append(soil); displace(g, .06, .6, 1)
    stone = noise_mat('stone', '#77786f', '#8d8e84', scale=5, bump=.4, rough=.8)
    for (x, y, r) in ((-.4, -1.6, .55), (.5, -.2, .5), (-.3, 1.3, .48), (.4, 2.9, .45)):
        o = cyl((x, y, .04), r, .12, stone, 32); o.scale = (1, .8, 1); displace(o, .03, .3, 1)
    random.seed(4)
    grass = mat('grass', '#2f4a2a', .9, .05); grass2 = mat('grass2', '#3d5e33', .9, .05)
    for i in range(160):
        side = random.choice((-1, 1)); x = side * random.uniform(1.6, 6); y = random.uniform(-3, 6.5)
        if random.random() < .35: x = random.uniform(-6, 6); y = random.uniform(5.2, 6.4)
        for k in range(5):
            h = random.uniform(.25, .6)
            cone((x + random.uniform(-.1, .1), y + random.uniform(-.1, .1), h / 2), .03, 0, h, grass if k % 2 else grass2, 4,
                 rot=(random.uniform(-.4, .4), random.uniform(-.4, .4), 0))
    bam = noise_mat('bamboo', '#7d6c43', '#958352', scale=8, bump=.2, rough=.7)
    for i in range(140):
        x = -8.4 + i * .12; cyl((x, 7, .85), .055, 1.7 + (i % 3) * .03, bam, 10)
    for z in (.5, 1.25):
        cyl((0, 6.92, z), .04, 17, mat('rope', '#3a2e22', .9, .05), 8, rot=(0, math.radians(90), 0))
    leaf = noise_mat('leaf', '#1f3326', '#2e4a36', scale=4, bump=.6, rough=.9)
    for (x, y, r) in ((-5, 10, 2.6), (-1.8, 11.5, 2.4), (1.5, 10.5, 2.2), (4.6, 10.8, 2.8), (7.5, 11, 2.4), (-7.8, 11, 2.3)):
        o = sphere((x, y, r * .9 + .8), (r, r * .8, r), leaf, 32); displace(o, .5, .7, 2)
    sk = sky_mat()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 24, 8), rotation=(math.radians(90), 0, 0)); p = bpy.context.object; p.scale = (60, 26, 1); p.data.materials.append(sk)
    star = emis('star', '#fff6d8', 3)
    for i in range(110):
        sphere((random.uniform(-14, 14), 23.8, random.uniform(5.2, 19)), (.025, .01, .025), star, 8)
    moon = emis('moon', '#fff3c8', 2.2)
    o = cyl((-3.4, 23.5, 12.5), .9, .1, moon, 64, rot=(math.radians(90), 0, 0))
    halo = bpy.data.materials.new('halo'); halo.use_nodes = True
    # veranda boards in the foreground
    wood = noise_mat('ver', '#6d4a2e', '#7f5836', scale=3, bump=.1, rough=.6)
    for i in range(6):
        box((0, -4.75 + i * .26 - 0.0, .42), (8, .24, .08), wood, .015, 2)
    box((0, -3.4, .32), (8, .16, .3), mat('beam', '#4e3420', .6, .1), .02, 2)
    pig(-.62, -4.05, .46, .4, math.radians(20))
    # wooden bucket (teoke) on the ground
    tb = noise_mat('teoke', '#a9824f', '#b98f58', scale=12, bump=.15)
    o = cyl((1.15, -1.2, .32), .45, .64, tb, 48); wtr = mat('water', '#1c2f52', .05, .6); cyl((1.15, -1.2, .645), .41, .02, wtr, 48)
    for z in (.14, .5): cyl((1.15, -1.2, z), .465, .06, mat('band', '#3b3b40', .4, .4), 48)
    # eave beam across the top
    box((0, -3.0, 4.15), (9, .3, .3), mat('eave', '#2c1e14', .7, .1), .02, 2)
    bpy.ops.object.camera_add(location=(0, -6.6, 1.75), rotation=(math.radians(84), 0, 0))
    c = bpy.context.object; c.data.lens = 26; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_width = 36; c.data.sensor_height = 36; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280
    sc.render.filepath = os.path.join(OUT, 'bg.png'); bpy.ops.render.render(write_still=True)
    print('wrote bg', flush=True)

def furin():
    sc = reset(); top_light(sc) if 'top_light' in globals() else None
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='AREA', location=(-1, -4, 2)); a = bpy.context.object; a.data.energy = 300; a.data.size = 3
    a.rotation_euler = Euler((math.radians(70), 0, math.radians(-15)))
    sc.cycles.film_transparent_glass = True
    glass = mat('glass', '#dff1f7', .08, .5)
    gb = glass.node_tree.nodes['Principled BSDF']; gb.inputs['Transmission Weight'].default_value = .75; gb.inputs['IOR'].default_value = 1.2
    sphere((0, 0, 0), (.42, .42, .4), glass, 48)
    bpy.ops.object.select_all(action='DESELECT')
    o = bpy.context.scene.objects[-1] if False else None
    # cut the bottom off the bell
    bell = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH'][0]
    bm_ = bmesh.new(); bm_.from_mesh(bell.data); bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z < -0.35], context='VERTS'); bm_.to_mesh(bell.data); bm_.free()
    sol = bell.modifiers.new('s', 'SOLIDIFY'); sol.thickness = .03
    red = mat('fishred', '#e0442e', .4, .2)
    for (a_, z) in ((-.5, -.02), (.6, .1)):
        x, y = math.sin(a_) * .41, -math.cos(a_) * .41
        sphere((x, y, z), (.09, .03, .05), red, 16, rot=(0, 0, a_))
        cone((x + math.cos(a_) * .1, y + math.sin(a_) * .1, z), .05, 0, .08, red, 8, rot=(0, math.radians(90), a_))
    cyl((0, 0, .44), .06, .1, mat('cap', '#c94b3a', .5, .2), 16)
    cyl((0, 0, .1), .008, .9, mat('str', '#efe6d4', .9, .0), 6)       # string down through the bell
    sphere((0, 0, -.32), (.05, .05, .05), glass, 16)                   # clapper
    # camera: front view
    bpy.ops.object.camera_add(location=(0, -10, 0.05), rotation=(math.radians(90), 0, 0))
    c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = 1.4; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 300, 300
    sc.render.filepath = os.path.join(OUT, 'furin.png'); bpy.ops.render.render(write_still=True)
    print('wrote furin', flush=True)

def pig_sprite():
    sc = reset()
    for o in list(sc.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o)
    bpy.ops.object.light_add(type='AREA', location=(1, -4, 3)); a = bpy.context.object; a.data.energy = 400; a.data.size = 3
    a.rotation_euler = Euler((math.radians(55), 0, math.radians(15)))
    pig(0, 0, 0, 1.0, math.radians(25))
    bpy.ops.object.camera_add(location=(0, -10, 1.5), rotation=(math.radians(84), 0, 0))
    c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = 1.9; sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = 300, 300
    sc.render.filepath = os.path.join(OUT, 'pig.png'); bpy.ops.render.render(write_still=True)
    print('wrote pig', flush=True)

JOBS = {'bg': bg, 'furin': furin}
for name, fn in JOBS.items():
    if WHAT in ('all', name): fn()
