# 「てのなるほうへ」の追跡者「テナガ」を作る。骨・ウェイト・アニメーション入りのGLBを書き出す。
# python3 chaser.py <outdir>   (needs `pip install bpy`)
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Matrix, noise

OUT = sys.argv[-1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24

# ---------------- skeleton (Blender: Z up, creature faces -Y) ----------------
B = {}          # name -> (head, tail, parent, radius_head, radius_tail)
ORDER = []
def bone(n, h, t, p=None, rh=0.05, rt=None):
    B[n] = (Vector(h), Vector(t), p, rh, rt if rt is not None else rh); ORDER.append(n)

bone('hips',  (0, 0.00, 1.18), (0, -0.02, 1.45), None, 0.12, 0.10)
bone('spine', (0, -0.02, 1.45), (0, -0.08, 1.74), 'hips', 0.10, 0.12)
bone('chest', (0, -0.08, 1.74), (0, -0.15, 1.98), 'spine', 0.12, 0.09)
bone('neck',  (0, -0.15, 1.98), (0, -0.29, 2.17), 'chest', 0.042, 0.036)
bone('head',  (0, -0.29, 2.17), (0, -0.37, 2.47), 'neck', 0.0, 0.0)
for s, x in (('L', 1), ('R', -1)):
    bone(f'shoulder.{s}', (0.05*x, -0.12, 1.93), (0.25*x, -0.11, 1.92), 'chest', 0.06, 0.05)
    bone(f'upperarm.{s}', (0.25*x, -0.11, 1.92), (0.33*x, -0.09, 1.36), f'shoulder.{s}', 0.045, 0.032)
    bone(f'forearm.{s}', (0.33*x, -0.09, 1.36), (0.38*x, -0.15, 0.84), f'upperarm.{s}', 0.032, 0.022)
    bone(f'hand.{s}', (0.38*x, -0.15, 0.84), (0.395*x, -0.165, 0.73), f'forearm.{s}', 0.026, 0.024)
    for i, fy in enumerate((-0.045, -0.015, 0.015, 0.045)):
        L = 0.17 + (0.03 if i in (1, 2) else 0)
        b0 = Vector((0.395*x, -0.165 + fy*0.6, 0.73))
        b1 = b0 + Vector((0.012*x, fy*0.5, -L))
        b2 = b1 + Vector((-0.006*x, fy*0.2 - 0.02, -L*0.85))
        bone(f'finger{i}a.{s}', b0, b1, f'hand.{s}', 0.010, 0.008)
        bone(f'finger{i}b.{s}', b1, b2, f'finger{i}a.{s}', 0.008, 0.004)
    bone(f'thigh.{s}', (0.11*x, 0.0, 1.2), (0.13*x, -0.06, 0.66), 'hips', 0.065, 0.04)
    bone(f'shin.{s}', (0.13*x, -0.06, 0.66), (0.13*x, 0.02, 0.1), f'thigh.{s}', 0.038, 0.025)
    bone(f'foot.{s}', (0.13*x, 0.02, 0.1), (0.13*x, -0.17, 0.02), f'shin.{s}', 0.03, 0.02)

# ---------------- body via skin modifier ----------------
verts, vrad, edges, key = [], [], [], {}
def vid(p, r):
    k = tuple(round(c, 4) for c in p)
    if k not in key:
        key[k] = len(verts); verts.append(p.copy()); vrad.append(r)
    else:
        vrad[key[k]] = max(vrad[key[k]], r)
    return key[k]
for n in ORDER:
    if n == 'head': continue
    h, t, p, rh, rt = B[n]
    if n.startswith('shoulder'): continue  # shoulders built from chest
    if n == 'chest':   # split so the shoulder bar can branch off
        m = vid(h.lerp(t, 0.75), 0.11)
        edges += [(vid(h, rh), m), (m, vid(t, rt))]
        continue
    a, b = vid(h, rh), vid(t, rt)
    edges.append((a, b))
# connect islands: pelvis -> thighs, hand -> fingers, chest -> shoulders
for s, x in (('L', 1), ('R', -1)):
    edges.append((vid(B['hips'][0], 0.12), vid(B[f'thigh.{s}'][0], 0.065)))
    for i in range(4):
        edges.append((vid(B[f'hand.{s}'][1], 0.024), vid(B[f'finger{i}a.{s}'][0], 0.010)))
    a = vid(B['chest'][0].lerp(B['chest'][1], 0.75), 0.1)
    b = vid(B[f'upperarm.{s}'][0], 0.05)
    edges.append((a, b))
me = bpy.data.meshes.new('body'); me.from_pydata([tuple(v) for v in verts], edges, [])
body = bpy.data.objects.new('body', me); sc.collection.objects.link(body)
sk = body.modifiers.new('skin', 'SKIN'); sk.branch_smoothing = 0.6; sk.use_smooth_shade = True
for i, r in enumerate(vrad):
    me.skin_vertices[0].data[i].radius = (r, r * 0.92)
# one root per connected island (islands without a root collapse)
adj = {i: set() for i in range(len(verts))}
for a, b in edges: adj[a].add(b); adj[b].add(a)
seen = set(); islands = 0
for i in range(len(verts)):
    if i in seen: continue
    islands += 1; me.skin_vertices[0].data[i].use_root = True
    st = [i]
    while st:
        j = st.pop()
        if j in seen: continue
        seen.add(j); st += list(adj[j])
print('skin islands', islands)
sub = body.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
dg = bpy.context.evaluated_depsgraph_get()
bm_me = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
bpy.data.objects.remove(body)
body = bpy.data.objects.new('body', bm_me); sc.collection.objects.link(body)

bm = bmesh.new(); bm.from_mesh(body.data); bm.normal_update()
for v in bm.verts:
    p, n = v.co, v.normal
    d = noise.noise(p * 9.0) * 0.004
    if 1.5 < p.z < 1.92 and abs(p.x) < 0.05 and n.y < -0.3 and p.z < 1.7: d -= 0.012   # sunken belly
    v.co = p + n * d
bm.to_mesh(body.data); bm.free()
for f in body.data.polygons: f.use_smooth = True

# ---------------- head ----------------
hb = B['head']
hc = hb[0].lerp(hb[1], 0.38)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=44, radius=0.122, location=(0, 0, 0))
head = bpy.context.active_object; head.name = 'head'
bm = bmesh.new(); bm.from_mesh(head.data)
EYES = [Vector((0.047, -0.112, 0.035)), Vector((-0.047, -0.112, 0.035))]
def mouth_y(x): return -0.065 + 1.6 * x * x   # grin curve (local z)
for v in bm.verts:
    p = v.co.copy()
    p.x *= 0.78; p.y *= 0.92; p.z *= 1.22
    if p.z < 0:                       # long jaw, pushed forward
        t = -p.z / 0.16
        p.y -= 0.035 * t
        p.x *= 1 - 0.25 * t
        p.z *= 1.25
    if p.z > 0.06: p.y += 0.02 * (p.z - 0.06) / 0.1   # sloped skull
    for e in EYES:                   # deep sockets
        dd = (Vector((p.x, p.y, p.z)) - e).length
        p += Vector((0, 1, 0)) * 0.07 * math.exp(-(dd / 0.03) ** 2)
    for cx in (0.068, -0.068):        # sunken cheeks
        dd = (Vector((p.x, p.y, p.z)) - Vector((cx, -0.09, -0.03))).length
        p += Vector((-cx, 0.5, 0)).normalized() * -0.02 * math.exp(-(dd / 0.035) ** 2)
    if p.y < -0.06 and 0.06 < p.z < 0.085: p.y -= 0.006   # brow ridge
    if p.y < -0.02:                  # ear-to-ear slit
        dz = p.z - mouth_y(p.x)
        if abs(p.x) < 0.11:
            gape = 0.017 * (1 - (p.x / 0.1) ** 2)                 # mouth hangs open in the middle
            p.y += 0.055 * math.exp(-(dz / max(0.008, gape)) ** 4) * (1 - abs(p.x) / 0.12)
    p += Vector((noise.noise(p * 30), noise.noise(p * 30 + Vector((5, 1, 3))), 0)) * 0.002
    v.co = p
bm.to_mesh(head.data); bm.free()
for f in head.data.polygons: f.use_smooth = True
head.location = hc
head.rotation_euler = (math.radians(-12), 0, 0)
# teeth along the grin
from mathutils.bvhtree import BVHTree
bm = bmesh.new(); bm.from_mesh(head.data); tree = BVHTree.FromBMesh(bm); bm.free()
teeth = []
for i in range(17):
    u = (i / 16 - 0.5) * 2
    x = u * 0.078 + random.uniform(-0.002, 0.002)
    for up in (1, -1):
        z = mouth_y(x) + up * (0.004 + 0.017 * max(0, 1 - (x / 0.1) ** 2))
        hit = tree.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
        y = (hit[0].y if hit[0] else -0.11) + 0.004
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.0048, radius2=0.0006, depth=0.016 + random.random() * 0.01,
                                        location=(x, y, z - up * 0.006))
        tt = bpy.context.active_object
        tt.rotation_euler = (math.pi if up > 0 else 0, random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        teeth.append(tt)
bpy.ops.object.select_all(action='DESELECT')
for tt in teeth: tt.select_set(True)
bpy.context.view_layer.objects.active = teeth[0]
bpy.ops.object.join()
teeth = bpy.context.active_object; teeth.name = 'teeth'
teeth.parent = head
eyes = []
for e in EYES:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0065, location=(e.x * 0.97, e.y + 0.05, e.z - 0.004))
    eyes.append(bpy.context.active_object)
bpy.ops.object.select_all(action='DESELECT')
for o in eyes: o.select_set(True)
bpy.context.view_layer.objects.active = eyes[0]; bpy.ops.object.join()
pupils = bpy.context.active_object; pupils.name = 'pupils'; pupils.parent = head
emat = bpy.data.materials.new('eye'); emat.use_nodes = True
eb_ = emat.node_tree.nodes['Principled BSDF']; eb_.inputs['Base Color'].default_value = (0.75, 0.72, 0.6, 1); eb_.inputs['Roughness'].default_value = 0.04
pupils.data.materials.append(emat)
bpy.context.view_layer.update()
for o in (head, teeth, pupils):
    o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix()

# ---------------- vertex colours ----------------
def paint(obj, fn):
    attr = obj.data.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            vi = obj.data.loops[li].vertex_index
            attr.data[li].color = (*fn(obj.data.vertices[vi].co, obj.data.vertices[vi].normal), 1.0)
def skin_col(p, n):
    m = noise.noise(p * 6) * 0.5 + noise.noise(p * 19) * 0.25
    base = Vector((0.40, 0.40, 0.36)) * (0.85 + m * 0.3)
    vein = max(0.0, 1 - abs(noise.noise(p * 14 + Vector((3, 3, 3)))) * 9)
    base = base.lerp(Vector((0.36, 0.38, 0.45)), vein * 0.35)
    if p.z < 0.75 and abs(p.x) > 0.3: base = base.lerp(Vector((0.18, 0.15, 0.13)), min(1, (0.75 - p.z) * 3))   # filthy fingers
    if p.z < 0.25: base = base.lerp(Vector((0.2, 0.17, 0.15)), (0.25 - p.z) * 3)                         # filthy feet
    if n.y > 0.3 and 1.3 < p.z < 2: base *= 0.92
    return tuple(max(0, min(1, c)) for c in base)
paint(body, skin_col)
def head_col(p, n):
    q = p - hc
    q = Matrix.Rotation(math.radians(12), 3, 'X') @ q
    c = Vector(skin_col(p, n))
    for e in EYES:
        dd = (q - e).length
        c = c.lerp(Vector((0.0, 0.0, 0.0)), min(1, math.exp(-(dd / 0.028) ** 2) * 2.2))
    if q.y < -0.02 and abs(q.x) < 0.11:
        dz = q.z - mouth_y(q.x)
        gape = max(0.008, 0.017 * (1 - (q.x / 0.1) ** 2))
        lip = math.exp(-(dz / (gape + 0.008)) ** 2)
        c = c.lerp(Vector((0.16, 0.03, 0.025)), min(1, lip * 1.5))
        c = c.lerp(Vector((0.005, 0.0, 0.0)), min(1, math.exp(-(dz / gape) ** 4) * 1.3))
        if dz < 0:   # dried drips below the grin
            streak = max(0, noise.noise(Vector((q.x * 70, 0, 0))) - 0.1) * 2.5
            c = c.lerp(Vector((0.22, 0.04, 0.03)), min(0.85, streak * math.exp(dz / 0.05)))
    return tuple(c)
paint(head, head_col)
paint(teeth, lambda p, n: (0.5, 0.44, 0.3))
paint(pupils, lambda p, n: (0.8, 0.78, 0.7))

# weights (computed per part, groups survive the join)
def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length, t
def weight(obj, only=None):
    for n in ORDER: obj.vertex_groups.new(name=n)
    for v in obj.data.vertices:
        if only: obj.vertex_groups[only].add([v.index], 1.0, 'REPLACE'); continue
        ds = []
        for n in ORDER:
            if n == 'head': continue
            d, t = seg_dist(v.co, B[n][0], B[n][1])
            ds.append((d, n, t))
        ds.sort()
        d1, n1, t1 = ds[0]
        res = {n1: 1.0}
        for d2, n2, t2 in ds[1:4]:
            related = B[n2][2] == n1 or B[n1][2] == n2
            if related and d2 < d1 * 1.6 + 0.02:
                w = max(0.0, 1 - (d2 - d1) / (d1 * 0.6 + 0.02)) * 0.5
                res[n2] = w; res[n1] = 1 - w
                break
        for n, w in res.items(): obj.vertex_groups[n].add([v.index], w, 'REPLACE')
weight(body); weight(head, 'head'); weight(teeth, 'head'); weight(pupils, 'head')
smat = bpy.data.materials.new('skin')
for o in (body, head, teeth): o.data.materials.clear(); o.data.materials.append(smat)

# ---------------- join + normal-map bake from a detailed high-poly copy ----------------
bpy.ops.object.select_all(action='DESELECT')
for o in (body, head, teeth, pupils): o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
mesh = bpy.context.active_object; mesh.name = 'TenagaMesh'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')
# give the face (seen up close in the jump scare) ~3x the texel density, then repack
bm = bmesh.new(); bm.from_mesh(mesh.data); uvl = bm.loops.layers.uv.active
for f in bm.faces:
    c = f.calc_center_median()
    if c.z > 2.08 and c.y < -0.12:
        for l in f.loops: l[uvl].uv *= 3.0
bm.to_mesh(mesh.data); bm.free()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')

JOINTS = [B[n][0] for n in ORDER if n.startswith(('forearm', 'shin', 'finger', 'hand'))]
def detail(p, n):
    d = 0.0
    w = 1 - abs(noise.noise(p * 38.0))                        # fine wrinkles
    d += (w ** 6) * 0.0035
    v = abs(noise.noise(p * 11.0 + Vector((7, 1, 2))))        # raised veins
    d += max(0, 0.05 - v) / 0.05 * 0.003
    d += noise.noise(p * 90.0) * 0.0004                       # pores
    if 1.48 < p.z < 1.92 and abs(p.x) < 0.17 and abs(p.x) > 0.022:   # ribs
        front = max(0.0, -n.y); side = abs(n.x)
        rib = (math.sin((p.z + abs(p.x) * 0.35) * 62.0) * 0.5 + 0.5) ** 3
        d += rib * 0.011 * min(1, front * 0.7 + side)
    if 1.2 < p.z < 2.05 and abs(p.x) < 0.035 and n.y > 0.4:    # spine knobs
        d += (math.sin(p.z * 68.0) * 0.5 + 0.5) ** 4 * 0.008
    if 1.86 < p.z < 1.95 and 0.03 < abs(p.x) < 0.2 and n.y < 0: d += 0.004   # collar bones
    for j in JOINTS:                                          # bony knuckles / elbows / knees
        dd = (p - j).length
        if dd < 0.05: d += 0.004 * math.exp(-(dd / 0.018) ** 2)
    if 1.97 < p.z < 2.2 and abs(p.x) < 0.06:                    # neck folds
        d += (math.sin(p.z * 140) * 0.5 + 0.5) ** 3 * 0.0018
    return d
high = mesh.copy(); high.data = mesh.data.copy(); high.name = 'high'; sc.collection.objects.link(high)
sd = high.modifiers.new('sd', 'SUBSURF'); sd.levels = 2
dg = bpy.context.evaluated_depsgraph_get()
hm = bpy.data.meshes.new_from_object(high.evaluated_get(dg)); high.modifiers.clear(); high.data = hm
bm = bmesh.new(); bm.from_mesh(high.data); bm.normal_update()
for v in bm.verts: v.co = v.co + v.normal * detail(v.co, v.normal)
bm.to_mesh(high.data); bm.free()
print('high verts', len(high.data.vertices))

sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
nimg = bpy.data.images.new('tenaga_normal', 1024, 1024, alpha=False); nimg.colorspace_settings.name = 'Non-Color'
mat = smat; mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
nt.links.new(ca.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.6
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = nimg; nt.nodes.active = tex
etex = emat.node_tree.nodes.new('ShaderNodeTexImage'); etex.image = nimg; emat.node_tree.nodes.active = etex
bpy.ops.object.select_all(action='DESELECT')
high.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = mesh
bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=0.012, max_ray_distance=0.03, margin=6)
nimg.filepath_raw = os.path.join(OUT, 'tenaga_normal.png'); nimg.file_format = 'PNG'; nimg.save()
# albedo: vertex colour x cavity occlusion x mottling, evaluated on the high-poly and baked down
hmat = bpy.data.materials.new('bakesrc'); hmat.use_nodes = True
hn = hmat.node_tree; hb_ = hn.nodes['Principled BSDF']
hc_ = hn.nodes.new('ShaderNodeVertexColor'); hc_.layer_name = 'Col'
ao = hn.nodes.new('ShaderNodeAmbientOcclusion'); ao.samples = 16; ao.inputs['Distance'].default_value = 0.04
pw = hn.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.6
hn.links.new(ao.outputs['AO'], pw.inputs[0])
nz = hn.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
ramp = hn.nodes.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value = 0.3; ramp.inputs['From Max'].default_value = 0.7
ramp.inputs['To Min'].default_value = 0.82; ramp.inputs['To Max'].default_value = 1.08
hn.links.new(nz.outputs['Fac'], ramp.inputs['Value'])
m1 = hn.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.blend_type = 'MULTIPLY'; m1.inputs['Factor'].default_value = 1
hn.links.new(hc_.outputs['Color'], m1.inputs['A']); hn.links.new(pw.outputs['Value'], m1.inputs['B'])
m2 = hn.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
hn.links.new(m1.outputs['Result'], m2.inputs['A']); hn.links.new(ramp.outputs['Result'], m2.inputs['B'])
hn.links.new(m2.outputs['Result'], hb_.inputs['Base Color'])
high.data.materials[0] = hmat
cimg = bpy.data.images.new('tenaga_albedo', 1024, 1024, alpha=False)
tex.image = cimg; nt.nodes.active = tex; etex.image = cimg
sc.cycles.samples = 16
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_selected_to_active=True, cage_extrusion=0.012, max_ray_distance=0.03, margin=6)
cimg.filepath_raw = os.path.join(OUT, 'tenaga_albedo.png'); cimg.file_format = 'PNG'; cimg.save()
tex.image = nimg; emat.node_tree.nodes.remove(etex)
ctex = nt.nodes.new('ShaderNodeTexImage'); ctex.image = cimg
nt.links.new(ctex.outputs['Color'], bsdf.inputs['Base Color'])
bpy.data.objects.remove(high)
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
nt.links.new(tex.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])

# ---------------- armature ----------------
arm_d = bpy.data.armatures.new('rig'); arm = bpy.data.objects.new('Tenaga', arm_d)
sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for n in ORDER:
    h, t, p, *_ = B[n]
    eb = arm_d.edit_bones.new(n); eb.head = h; eb.tail = t
    eb.align_roll(Vector((0, -1, 0)) if abs((t - h).normalized().y) < 0.9 else Vector((0, 0, 1)))
    if p: eb.parent = arm_d.edit_bones[p]; eb.use_connect = (eb.head - arm_d.edit_bones[p].tail).length < 1e-4
bpy.ops.object.mode_set(mode='OBJECT')

mesh.parent = arm
mod = mesh.modifiers.new('arm', 'ARMATURE'); mod.object = arm
print('tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))

# ---------------- animation ----------------
P = arm.pose.bones
for pb in P: pb.rotation_mode = 'XYZ'
def clear():
    for pb in P: pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
def key(f):
    for pb in P:
        pb.keyframe_insert('rotation_euler', frame=f)
        if pb.name == 'hips': pb.keyframe_insert('location', frame=f)
def R(n, x=0, y=0, z=0):
    P[n].rotation_euler = (x, y, z)
def mirror_sign(s): return 1 if s == 'L' else -1

# figure out sign so that +swing moves the limb forward (-Y)
clear(); R('thigh.L', 0.6); bpy.context.view_layer.update()
SW = 1 if (arm.matrix_world @ P['shin.L'].tail).y < (arm.matrix_world @ P['shin.R'].tail).y else -1
clear(); R('upperarm.L', z=0.5); bpy.context.view_layer.update()
SIDE = 1 if (P['forearm.L'].tail).x > (P['forearm.R'].tail).x * -1 else -1
print('swing sign', SW, 'side sign', SIDE)

def fingers(s, curl):
    for i in range(4):
        R(f'finger{i}a.{s}', -SW * curl * (0.8 + 0.1 * i)); R(f'finger{i}b.{s}', -SW * curl * 1.1)

def base_pose(t, hunch=0.35):
    R('spine', SW * hunch * 0.4); R('chest', SW * hunch * 0.5); R('neck', -SW * hunch * 0.6); R('head', -SW * hunch * 0.3)
    for s in 'LR':
        m = mirror_sign(s)
        R(f'shoulder.{s}', 0, 0, 0)

def make(name, frames, fn, loop=True):
    act = bpy.data.actions.new(name); act.use_fake_user = True
    arm.animation_data_create(); arm.animation_data.action = act
    for f in range(0, frames + 1, 2 if frames > 30 else 1):
        clear(); fn(f / frames); key(f)
    for fc in getattr(act, 'fcurves', []):
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    return act

def walk(t, run=False):
    ph = t * 2 * math.pi
    amp = 0.85 if run else 0.5
    base_pose(t, 0.7 if run else 0.4)
    for s in 'LR':
        o = 0 if s == 'L' else math.pi
        m = mirror_sign(s)
        sw = math.sin(ph + o)
        R(f'thigh.{s}', SW * sw * amp - SW * (0.25 if run else 0.05), 0, m * 0.04)
        knee = max(0, math.sin(ph + o + 1.4)) * (1.4 if run else 0.9) + 0.15
        R(f'shin.{s}', -SW * knee)
        R(f'foot.{s}', SW * (0.25 * math.sin(ph + o + 0.6)))
        # dangling arms, lag behind
        a = -math.sin(ph + o - 0.4) * (0.6 if run else 0.25)
        if run: a -= 0.5
        R(f'upperarm.{s}', SW * a, 0, SIDE * m * (0.12 + (0.25 if run else 0.04)))
        R(f'forearm.{s}', SW * (0.25 + (0.9 if run else 0.15) + 0.1 * math.sin(ph + o - 1.2)))
        R(f'hand.{s}', SW * 0.1 * math.sin(ph + o - 1.8))
        fingers(s, 0.15 + 0.1 * math.sin(ph + o))
    bob = abs(math.sin(ph)) * (0.06 if run else 0.035)
    P['hips'].location = (0, bob, 0)                     # bone local Y = up for hips
    R('hips', SW * (0.25 if run else 0.05), math.sin(ph) * (0.18 if run else 0.12), 0)
    R('head', -SW * 0.25 + 0.08 * math.sin(ph * 2), 0.12 * math.sin(ph * 0.5 + 1), 0.3 * math.sin(ph * 0.5) * (0 if run else 1))
make('walk', 48, lambda t: walk(t, False))
make('run', 18, lambda t: walk(t, True))

def idle(t):
    ph = t * 2 * math.pi
    base_pose(t, 0.45)
    for s in 'LR':
        m = mirror_sign(s)
        R(f'upperarm.{s}', SW * 0.05 * math.sin(ph + (0 if s == 'L' else 1)), 0, SIDE * m * 0.05)
        R(f'forearm.{s}', SW * 0.2); fingers(s, 0.2 + 0.15 * math.sin(ph * 3 + m))
        R(f'thigh.{s}', -SW * 0.08); R(f'shin.{s}', -SW * 0.18)
    # slow listening head tilt, with an unnatural snap halfway
    tilt = 0.5 * math.sin(ph) if t < 0.5 else 0.6 * math.sin(ph * 3)
    R('neck', -SW * 0.3, 0, 0.4 * math.sin(ph))
    R('head', -SW * 0.2, tilt * 0.8, 0.3 * math.sin(ph + 0.5))
    P['hips'].location = (0, -0.03, 0)
make('idle', 96, idle)

def clap(t):
    # raise both long arms forward then clap twice
    base_pose(t, 0.5)
    lift = min(1, t / 0.3)
    hit = 0
    for c in (0.42, 0.62):
        hit = max(hit, math.exp(-((t - c) / 0.04) ** 2))
    if t > 0.8: lift = max(0, 1 - (t - 0.8) / 0.2)
    for s in 'LR':
        m = mirror_sign(s)
        R(f'shoulder.{s}', 0, 0, 0)
        R(f'upperarm.{s}', SW * 1.55 * lift, 0, SIDE * -m * (0.25 + 0.2 * hit) * lift)
        R(f'forearm.{s}', SW * 0.35 * lift, 0, SIDE * -m * 0.3 * lift)
        R(f'hand.{s}', 0, 0, SIDE * -m * 0.3 * lift); fingers(s, 0.05)
        R(f'thigh.{s}', -SW * 0.06); R(f'shin.{s}', -SW * 0.15)
    R('neck', -SW * 0.6 * lift, 0, 0); R('head', SW * 0.3 * lift, 0.15 * hit, 0)
make('clap', 40, clap)

def grab(t):
    # folds down to the victim's face: knees bend, spine curls forward, head tilts up to stare, arms wrap around
    k = min(1, t / 0.3); k = k * k * (3 - 2 * k)
    for s in 'LR':
        m = mirror_sign(s)
        R(f'upperarm.{s}', SW * (1.25 * k), 0, SIDE * m * 0.75 * k)
        R(f'forearm.{s}', SW * 0.15 * k, 0, SIDE * -m * 0.9 * k)
        R(f'hand.{s}', 0, 0, SIDE * -m * 0.4 * k)
        fingers(s, -0.15 * k + 1.0 * max(0, (t - 0.55) * 2))
        R(f'thigh.{s}', SW * 0.55 * k, 0, m * 0.12 * k); R(f'shin.{s}', -SW * 0.95 * k); R(f'foot.{s}', SW * 0.35 * k)
    R('hips', SW * 0.25 * k)
    R('spine', SW * 0.45 * k); R('chest', SW * 0.45 * k)
    R('neck', -SW * 0.35 * k); R('head', -SW * 0.75 * k, 0.35 * k * math.sin(t * 9), 0.15 * k * math.sin(t * 23))
    P['hips'].location = (0, -0.18 * k, 0)
make('grab', 24, grab, False)

arm.animation_data.action = bpy.data.actions['grab']; sc.frame_set(24); bpy.context.view_layer.update()
print('mats', [m.name if m else None for m in mesh.data.materials], sorted(set(p.material_index for p in mesh.data.polygons))); print('grab head', tuple(round(c, 2) for c in (arm.matrix_world @ P['head'].head)), 'eye-level target ~1.6')
arm.animation_data.action = bpy.data.actions['walk']

# ---------------- export ----------------
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'tenaga.glb'), export_format='GLB', use_selection=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_skins=True,
                          export_vertex_color='MATERIAL', export_yup=True, export_apply=False,
                          export_optimize_animation_size=True, export_image_format='JPEG', export_jpeg_quality=82)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'tenaga.blend'))
print('done')
