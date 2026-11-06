# 校舎の小道具（ロッカー・机・いす・引き戸・鍵・電池・下駄箱・昇降口の扉・窓・蛍光灯）を作って props.glb に書き出す。
# 材質は名前だけ付けて書き出し、ゲーム側で textures.py の焼き込みテクスチャに差し替える。
# python3 props.py <outdir>   (needs `pip install bpy`)
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

MATS = {}
def M(name, col=(0.5, 0.5, 0.5), rough=0.6, metal=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    MATS[name] = m; return m
for n, c, r, mt, a in [('wood', (0.4, 0.26, 0.13), 0.5, 0, 1), ('metal', (0.33, 0.36, 0.33), 0.5, 0.3, 1),
                       ('steel', (0.5, 0.5, 0.5), 0.35, 0.8, 1), ('glass', (0.05, 0.07, 0.08), 0.05, 0, 0.35),
                       ('brass', (0.7, 0.5, 0.2), 0.3, 1, 1), ('red', (0.5, 0.04, 0.03), 0.5, 0, 1),
                       ('white', (0.75, 0.74, 0.7), 0.6, 0, 1), ('black', (0.02, 0.02, 0.02), 0.8, 0, 1),
                       ('battery', (0.05, 0.08, 0.2), 0.4, 0.2, 1), ('chain', (0.3, 0.3, 0.32), 0.4, 0.9, 1)]:
    M(n, c, r, mt, a)

parts = []
def box(sx, sy, sz, x, y, z, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    o = bpy.context.active_object; o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(MATS[mat]); parts.append(o); return o
def cyl(r, d, x, y, z, mat, rot=(0, 0, 0), v=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=(x, y, z), rotation=rot)
    o = bpy.context.active_object; o.data.materials.append(MATS[mat]); parts.append(o); return o
def tor(R, r, x, y, z, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=16, minor_segments=6, location=(x, y, z), rotation=rot)
    o = bpy.context.active_object; o.data.materials.append(MATS[mat]); parts.append(o); return o
def done(name, origin=(0, 0, 0)):
    global parts
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; o.data.name = name
    o.data.transform(Matrix.Translation(-Vector(origin)))
    o.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=False, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for f in o.data.polygons: f.use_smooth = False
    parts = []; return o

# ---- locker (掃除用具入れ): 0.6 x 0.5 x 1.8, open front; door hinged on its left edge ----
T = 0.015
box(0.6, 0.5, T, 0, 0, T / 2, 'metal'); box(0.6, 0.5, T, 0, 0, 1.8 - T / 2, 'metal')
box(T, 0.5, 1.8, -0.3 + T / 2, 0, 0.9, 'metal'); box(T, 0.5, 1.8, 0.3 - T / 2, 0, 0.9, 'metal')
box(0.6, T, 1.8, 0, 0.25 - T / 2, 0.9, 'metal')
box(0.04, 0.03, 0.5, 0.18, -0.12, 0.6, 'steel')            # a broom leaning inside
box(0.25, 0.03, 0.08, 0.18, -0.12, 0.33, 'black')
done('locker')
box(0.58, 0.02, 1.76, 0.29, 0, 0.9, 'metal')
for i in range(6):                                          # vent slits
    box(0.34, 0.012, 0.012, 0.29, -0.012, 1.35 + i * 0.045, 'black')
    box(0.34, 0.012, 0.012, 0.29, -0.012, 0.35 + i * 0.045, 'black')
box(0.03, 0.03, 0.12, 0.52, -0.02, 1.0, 'steel')
box(0.1, 0.004, 0.06, 0.29, -0.012, 1.62, 'white')         # faded name card
done('locker_door')                                          # hinge on its x=0 edge; the game puts it on the locker's open front

# ---- pupil desk + chair ----
box(0.65, 0.45, 0.025, 0, 0, 0.7, 'wood')
box(0.6, 0.38, 0.012, 0, 0.02, 0.6, 'metal'); box(0.6, 0.012, 0.09, 0, 0.21, 0.645, 'metal')
for sx in (-1, 1):
    for sy in (-1, 1):
        cyl(0.012, 0.69, sx * 0.29, sy * 0.19, 0.345, 'steel', v=8)
    box(0.012, 0.4, 0.012, sx * 0.29, 0, 0.08, 'steel')
done('desk')
box(0.38, 0.36, 0.02, 0, 0, 0.42, 'wood'); box(0.36, 0.02, 0.2, 0, 0.17, 0.72, 'wood')
for sx in (-1, 1):
    for sy in (-1, 1):
        cyl(0.011, 0.42, sx * 0.17, sy * 0.16, 0.21, 'steel', v=8)
    cyl(0.011, 0.34, sx * 0.17, 0.17, 0.6, 'steel', v=8)
done('chair')
# teacher's desk
box(1.2, 0.6, 0.03, 0, 0, 0.74, 'wood'); box(1.18, 0.02, 0.62, 0, -0.29, 0.42, 'metal')
box(0.02, 0.58, 0.72, -0.58, 0, 0.37, 'metal'); box(0.02, 0.58, 0.72, 0.58, 0, 0.37, 'metal')
box(0.4, 0.55, 0.15, 0.36, 0, 0.64, 'metal')
done('tdesk')

# ---- sliding classroom door 0.9 x 1.95 ----
box(0.9, 0.04, 0.07, 0, 0, 0.035, 'wood'); box(0.9, 0.04, 0.07, 0, 0, 1.915, 'wood')
box(0.07, 0.04, 1.95, -0.415, 0, 0.975, 'wood'); box(0.07, 0.04, 1.95, 0.415, 0, 0.975, 'wood')
box(0.76, 0.03, 0.85, 0, 0, 0.5, 'wood'); box(0.76, 0.04, 0.06, 0, 0, 0.95, 'wood')
box(0.76, 0.01, 0.9, 0, 0, 1.43, 'glass')
box(0.03, 0.05, 0.12, 0.33, 0, 1.0, 'black')
done('door')

# ---- key (brass, with a red tag) ----
tor(0.012, 0.003, 0, 0, 0.075, 'brass', rot=(math.pi / 2, 0, 0))
cyl(0.0028, 0.05, 0, 0, 0.04, 'brass', v=8)
box(0.004, 0.01, 0.006, 0, 0.006, 0.022, 'brass'); box(0.004, 0.008, 0.005, 0, 0.005, 0.031, 'brass')
tor(0.008, 0.0015, 0, 0, 0.096, 'chain', rot=(0, math.pi / 2, 0))
box(0.003, 0.03, 0.05, 0, 0, 0.13, 'red')
done('key')
cyl(0.007, 0.05, 0, 0, 0.025, 'battery', v=12); cyl(0.0025, 0.004, 0, 0, 0.052, 'steel', v=8)
done('battery')

# ---- shoe cubbies (下駄箱) 1.8 x 0.36 x 1.8 ----
box(1.8, 0.36, 0.02, 0, 0, 0.01, 'wood'); box(1.8, 0.36, 0.02, 0, 0, 1.79, 'wood'); box(1.8, 0.02, 1.8, 0, 0.17, 0.9, 'wood')
for i in range(7): box(0.02, 0.36, 1.8, -0.9 + i * 0.3, 0, 0.9, 'wood')
for j in range(1, 6): box(1.8, 0.36, 0.015, 0, 0, j * 0.3, 'wood')
import random; random.seed(3)
for i in range(6):
    for j in range(6):
        if random.random() < 0.35:   # a few forgotten indoor shoes
            box(0.1, 0.24, 0.07, -0.75 + i * 0.3 + random.uniform(-0.03, 0.03), -0.02, j * 0.3 + 0.05, 'white')
done('shoerack')

# ---- front entrance double door, chained shut with three padlocks ----
for sx in (-1, 1):
    x = sx * 0.45
    box(0.9, 0.05, 0.06, x, 0, 0.03, 'steel'); box(0.9, 0.05, 0.06, x, 0, 2.07, 'steel')
    box(0.06, 0.05, 2.1, x - 0.42, 0, 1.05, 'steel'); box(0.06, 0.05, 2.1, x + 0.42, 0, 1.05, 'steel')
    box(0.8, 0.01, 2.0, x, 0, 1.05, 'glass')
    box(0.03, 0.06, 0.5, sx * 0.08, -0.05, 1.05, 'steel')
for i in range(9):                                         # chain looped through the handles
    a = i / 8
    tor(0.025, 0.006, -0.1 + a * 0.2, -0.09, 1.25 - math.sin(a * math.pi) * 0.12, 'chain', rot=(0, 0, (i % 2) * math.pi / 2))
done('exitdoor')
for k in range(3):
    box(0.06, 0.03, 0.055, 0, 0, 0, 'brass'); tor(0.02, 0.005, 0, 0, 0.035, 'steel', rot=(math.pi / 2, 0, 0))
    done(f'padlock{k}')

# ---- aluminium window 1.0 x 1.3, two panes ----
box(1.0, 0.07, 0.04, 0, 0, 0.02, 'steel'); box(1.0, 0.07, 0.04, 0, 0, 1.28, 'steel')
box(0.04, 0.07, 1.3, -0.48, 0, 0.65, 'steel'); box(0.04, 0.07, 1.3, 0.48, 0, 0.65, 'steel')
box(0.03, 0.08, 1.3, 0, 0, 0.65, 'steel')
box(0.46, 0.01, 1.22, -0.24, 0.01, 0.65, 'glass'); box(0.46, 0.01, 1.22, 0.24, -0.01, 0.65, 'glass')
done('window')

# ---- dead fluorescent fixture ----
box(1.25, 0.16, 0.06, 0, 0, -0.03, 'white'); cyl(0.013, 1.2, 0, 0, -0.07, 'white', rot=(0, math.pi / 2, 0), v=8)
done('lamp')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'props.glb'), export_format='GLB', use_selection=True,
                          export_yup=True, export_apply=True, export_materials='EXPORT')
print('done', [o.name for o in bpy.data.objects])
