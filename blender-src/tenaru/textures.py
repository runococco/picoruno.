# 旧校舎の壁・床・天井・黒板などのシームレステクスチャを Blender のノードで作って焼き込む。
# python3 textures.py <outdir> [size]   (needs `pip install bpy`)
# Noise is sampled on a 4D torus (u,v -> cos/sin pairs) so every map tiles without seams.
import bpy, math, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 512
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.active_object
TAU = math.tau


class G:
    """tiny node-graph helper"""
    def __init__(self, name):
        self.m = bpy.data.materials.new(name); self.m.use_nodes = True
        self.t = self.m.node_tree; self.t.nodes.clear()
        self.out = self.t.nodes.new('ShaderNodeOutputMaterial')
        tc = self.t.nodes.new('ShaderNodeTexCoord')
        sep = self.t.nodes.new('ShaderNodeSeparateXYZ'); self.t.links.new(tc.outputs['UV'], sep.inputs[0])
        self.u, self.v = sep.outputs[0], sep.outputs[1]

    def link(self, a, b):
        self.t.links.new(a, b)

    def val(self, x):
        if isinstance(x, (int, float)):
            n = self.t.nodes.new('ShaderNodeValue'); n.outputs[0].default_value = x; return n.outputs[0]
        return x

    def math(self, op, a, b=0.0, c=None):
        n = self.t.nodes.new('ShaderNodeMath'); n.operation = op
        for i, x in enumerate((a, b) if c is None else (a, b, c)):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: self.link(x, n.inputs[i])
        return n.outputs[0]

    def add(self, a, b): return self.math('ADD', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def sub(self, a, b): return self.math('SUBTRACT', a, b)

    def torus(self, ru, rv, u=None, v=None, off=0.0):
        u = u or self.u; v = v or self.v
        a = self.mul(u, TAU); b = self.mul(v, TAU)
        cu = self.mul(self.math('COSINE', a), ru); su = self.mul(self.math('SINE', a), ru)
        cv = self.add(self.mul(self.math('COSINE', b), rv), off); sv = self.mul(self.math('SINE', b), rv)
        comb = self.t.nodes.new('ShaderNodeCombineXYZ')
        self.link(cu, comb.inputs[0]); self.link(su, comb.inputs[1]); self.link(cv, comb.inputs[2])
        return comb.outputs[0], sv

    def noise(self, ru, rv=None, detail=4, rough=0.55, off=0.0, u=None, v=None, distort=0.0):
        vec, w = self.torus(ru, rv if rv is not None else ru, u, v, off)
        n = self.t.nodes.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D'
        self.link(vec, n.inputs['Vector']); self.link(w, n.inputs['W'])
        n.inputs['Scale'].default_value = 1.0; n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough; n.inputs['Distortion'].default_value = distort
        return n.outputs['Fac']

    def voronoi(self, r, feature='F1', off=0.0, out='Distance'):
        vec, w = self.torus(r, r, off=off)
        n = self.t.nodes.new('ShaderNodeTexVoronoi'); n.voronoi_dimensions = '4D'; n.feature = feature
        self.link(vec, n.inputs['Vector']); self.link(w, n.inputs['W']); n.inputs['Scale'].default_value = 1.0
        return n.outputs[out]

    def white(self, a, b=None):
        n = self.t.nodes.new('ShaderNodeTexWhiteNoise'); n.noise_dimensions = '2D' if b is not None else '1D'
        if b is not None:
            comb = self.t.nodes.new('ShaderNodeCombineXYZ'); self.link(a, comb.inputs[0]); self.link(b, comb.inputs[1])
            self.link(comb.outputs[0], n.inputs['Vector'])
        else:
            self.link(a, n.inputs['W'])
        return n.outputs['Value']

    def ramp(self, fac, stops):
        n = self.t.nodes.new('ShaderNodeValToRGB'); cr = n.color_ramp
        while len(cr.elements) > 1: cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
        for p, c in stops[1:]:
            e = cr.elements.new(p); e.color = (*c, 1)
        self.link(fac, n.inputs[0]); return n.outputs[0]

    def mix(self, a, b, f, mode='MIX'):
        n = self.t.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = mode
        for sock, x in ((n.inputs['Factor'], f), (n.inputs['A'], a), (n.inputs['B'], b)):
            if isinstance(x, (int, float)): sock.default_value = x
            elif isinstance(x, tuple): sock.default_value = (*x, 1)
            else: self.link(x, sock)
        return n.outputs['Result']

    def smooth(self, x, e0, e1):   # smoothstep-ish via map range
        n = self.t.nodes.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'
        self.link(x, n.inputs['Value']); n.inputs['From Min'].default_value = e0; n.inputs['From Max'].default_value = e1
        return n.outputs['Result']

    def finish(self, color, height, rough=None, bump=1.0):
        self.color, self.height, self.rough, self.bump = color, height, rough, bump


def bake(g, name):
    """bake colour (emit), tangent normal (from bump) and roughness"""
    t = g.t
    img = lambda n, nc: bpy.data.images.new(n, SIZE, SIZE, alpha=False, is_data=nc)
    plane.data.materials.clear(); plane.data.materials.append(g.m)
    tex = t.nodes.new('ShaderNodeTexImage')
    def go(kind, image):
        tex.image = image; t.nodes.active = tex
        bpy.ops.object.bake(type=kind, margin=0)
        image.filepath_raw = os.path.join(OUT, image.name + '.png'); image.file_format = 'PNG'; image.save()
    em = t.nodes.new('ShaderNodeEmission')
    g.link(g.color, em.inputs['Color']); g.link(em.outputs[0], g.out.inputs['Surface'])
    go('EMIT', img(name + '_c', False))
    if g.rough is not None:
        g.link(g.rough, em.inputs['Color']); go('EMIT', img(name + '_r', True))
    bsdf = t.nodes.new('ShaderNodeBsdfPrincipled')
    bp = t.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = g.bump; bp.inputs['Distance'].default_value = 0.02
    g.link(g.height, bp.inputs['Height']); g.link(bp.outputs['Normal'], bsdf.inputs['Normal'])
    g.link(bsdf.outputs[0], g.out.inputs['Surface'])
    go('NORMAL', img(name + '_n', True))
    print('baked', name)


# ---------- wooden corridor floor: narrow waxed planks, scuffed down the middle ----------
g = G('floor')
PL = 6                                               # planks across the tile
pi = g.math('FLOOR', g.mul(g.u, PL))
pu = g.math('FRACT', g.mul(g.u, PL))
hsh = g.white(pi)
pv = g.math('FRACT', g.add(g.mul(g.v, 2), hsh))     # two joints per plank per tile
row = g.math('FLOOR', g.add(g.mul(g.v, 2), hsh))
tone = g.white(pi, g.math('MODULO', row, 2))
gap = g.math('MAXIMUM', g.sub(1, g.smooth(pu, 0.0, 0.035)), g.smooth(pu, 0.965, 1.0))
joint = g.math('MAXIMUM', g.sub(1, g.smooth(pv, 0.0, 0.01)), g.smooth(pv, 0.99, 1.0))
grain = g.noise(40, 2.0, detail=6, rough=0.6, off=g.mul(tone, 13))
wood = g.ramp(g.add(g.mul(grain, 0.7), g.mul(tone, 0.3)), [(0.25, (0.16, 0.08, 0.035)), (0.5, (0.32, 0.17, 0.08)), (0.75, (0.42, 0.25, 0.12))])
dirt = g.noise(5, 5, detail=8, rough=0.6, off=5)
grime = g.smooth(dirt, 0.5, 0.85)
col = g.mix(wood, (0.07, 0.05, 0.035), g.mul(grime, 0.45))
col = g.mix(col, (0.03, 0.02, 0.015), g.math('MAXIMUM', gap, joint))
h = g.sub(g.mul(grain, 0.15), g.math('MAXIMUM', gap, joint))
g.finish(col, h, rough=g.ramp(grime, [(0.0, (0.35,) * 3), (1.0, (0.75,) * 3)]), bump=0.6)
bake(g, 'floor')

# ---------- upper wall: cream plaster with water stains and hairline cracks ----------
g = G('wall')
n1 = g.noise(4, 4, detail=8, rough=0.6)
stain = g.smooth(g.noise(1.5, 3.0, detail=5, rough=0.7, off=3), 0.5, 0.75)
crack = g.smooth(g.voronoi(5, 'DISTANCE_TO_EDGE', off=2), 0.012, 0.0)
crack = g.mul(crack, g.smooth(g.noise(2, 2, off=9), 0.55, 0.65))
base = g.ramp(n1, [(0.3, (0.55, 0.53, 0.47)), (0.7, (0.66, 0.64, 0.57))])
col = g.mix(base, (0.36, 0.31, 0.22), g.mul(stain, 0.6))
streak = g.smooth(g.noise(10, 0.6, detail=3, off=7), 0.55, 0.8)    # drips run down (v)
col = g.mix(col, (0.3, 0.27, 0.2), g.mul(streak, 0.35))
col = g.mix(col, (0.12, 0.11, 0.1), crack)
g.finish(col, g.sub(g.mul(n1, 0.2), crack), rough=g.val(0.9), bump=0.5)
bake(g, 'wall')

# ---------- wainscot: pale green painted boards, chipped to dark wood ----------
g = G('wains')
bi = g.math('FRACT', g.mul(g.u, 8))
seam = g.math('MAXIMUM', g.sub(1, g.smooth(bi, 0, 0.03)), g.smooth(bi, 0.97, 1))
chips = g.smooth(g.noise(6, 6, detail=8, rough=0.7, off=4), 0.62, 0.66)
paint = g.ramp(g.noise(5, 5, detail=4), [(0.3, (0.33, 0.42, 0.36)), (0.7, (0.4, 0.5, 0.43))])
col = g.mix(paint, (0.12, 0.08, 0.05), chips)
scuff = g.smooth(g.sub(1, g.v), 0.8, 1.0)                    # kick marks along the bottom
col = g.mix(col, (0.1, 0.1, 0.09), g.mul(scuff, g.mul(g.noise(12, 3, off=1), 0.9)))
col = g.mix(col, (0.05, 0.05, 0.04), seam)
g.finish(col, g.sub(g.mul(g.sub(1, chips), 0.3), seam), rough=g.mix((0.4,) * 3, (0.85,) * 3, chips), bump=0.7)
bake(g, 'wains')

# ---------- ceiling: perforated acoustic board, sagging stains ----------
g = G('ceil')
cu = g.math('FRACT', g.mul(g.u, 2)); cv = g.math('FRACT', g.mul(g.v, 2))
edge = g.math('MAXIMUM', g.math('MAXIMUM', g.sub(1, g.smooth(cu, 0, 0.012)), g.smooth(cu, 0.988, 1)),
              g.math('MAXIMUM', g.sub(1, g.smooth(cv, 0, 0.012)), g.smooth(cv, 0.988, 1)))
hu = g.math('FRACT', g.mul(g.u, 48)); hv = g.math('FRACT', g.mul(g.v, 48))
hole = g.smooth(g.math('ADD', g.math('POWER', g.sub(hu, 0.5), 2), g.math('POWER', g.sub(hv, 0.5), 2)), 0.03, 0.02)
stain = g.smooth(g.noise(2, 2, detail=6, rough=0.7, off=8), 0.55, 0.72)
col = g.ramp(g.noise(8, 8), [(0.3, (0.6, 0.59, 0.55)), (0.7, (0.68, 0.67, 0.63))])
col = g.mix(col, (0.38, 0.3, 0.2), g.mul(stain, 0.7))
col = g.mix(col, (0.2, 0.2, 0.19), g.math('MAXIMUM', g.mul(hole, 0.8), edge))
g.finish(col, g.sub(0, g.math('MAXIMUM', hole, edge)), rough=g.val(0.95), bump=0.6)
bake(g, 'ceil')

# ---------- chalkboard: dark green with erased chalk ghosts ----------
g = G('board')
smear = g.noise(3, 1.2, detail=6, rough=0.6, off=2)
lines = g.smooth(g.noise(30, 6, detail=2, off=6, distort=2.0), 0.62, 0.7)     # scribble remains
col = g.ramp(g.noise(6, 6), [(0.3, (0.05, 0.12, 0.09)), (0.7, (0.07, 0.15, 0.11))])
col = g.mix(col, (0.32, 0.36, 0.33), g.mul(g.smooth(smear, 0.5, 0.8), 0.35))
col = g.mix(col, (0.55, 0.57, 0.53), g.mul(lines, 0.45))
g.finish(col, g.mul(smear, 0.05), rough=g.val(0.8), bump=0.2)
bake(g, 'board')

# ---------- painted steel (lockers, shoe racks): grey-green paint, rust blooms ----------
g = G('metal')
rust = g.smooth(g.noise(5, 5, detail=8, rough=0.7, off=1), 0.6, 0.72)
drip = g.smooth(g.noise(14, 1.0, detail=3, off=3), 0.6, 0.75)
paint = g.ramp(g.noise(10, 10, detail=3), [(0.3, (0.3, 0.33, 0.31)), (0.7, (0.36, 0.39, 0.36))])
rc = g.ramp(g.noise(30, 30, detail=6), [(0.3, (0.18, 0.07, 0.03)), (0.7, (0.35, 0.15, 0.06))])
col = g.mix(paint, rc, g.math('MAXIMUM', rust, g.mul(drip, 0.5)))
g.finish(col, g.mul(rust, 0.2), rough=g.mix((0.45,) * 3, (0.9,) * 3, rust), bump=0.5)
bake(g, 'metal')

# ---------- door / furniture wood: lighter, varnished, worn ----------
g = G('wood')
grain = g.noise(28, 1.5, detail=7, rough=0.6, distort=0.4)
col = g.ramp(grain, [(0.3, (0.3, 0.18, 0.09)), (0.5, (0.42, 0.27, 0.14)), (0.7, (0.5, 0.33, 0.18))])
wear = g.smooth(g.noise(4, 4, detail=6, off=5), 0.55, 0.8)
col = g.mix(col, (0.12, 0.08, 0.05), g.mul(wear, 0.35))
g.finish(col, g.mul(grain, 0.1), rough=g.mix((0.35,) * 3, (0.8,) * 3, wear), bump=0.4)
bake(g, 'wood')
print('done')
