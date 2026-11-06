# BGM + jingles for mikan.html: a slow, cosy kotatsu tune (electric piano, vibraphone, soft bass, brushes),
# rendered with FluidSynth / FluidR3_GM.   python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 84
CH = {'F': ['F3', 'A3', 'C4', 'E4'], 'Dm': ['D3', 'F3', 'A3', 'C4'], 'Bb': ['Bb2', 'D3', 'F3', 'A3'], 'C': ['C3', 'E3', 'G3', 'Bb3'],
      'Am': ['A2', 'C3', 'E3', 'G3'], 'Gm': ['G2', 'Bb2', 'D3', 'F3']}
ROOT = {'F': 'F1', 'Dm': 'D2', 'Bb': 'Bb1', 'C': 'C2', 'Am': 'A1', 'Gm': 'G1'}
PROG = ['F', 'Dm', 'Bb', 'C', 'F', 'Am', 'Gm', 'C'] * 2
A = ['C5:3 A4:1 C5:2 D5:2', 'F5:4 E5:2 D5:2', 'D5:3 C5:1 Bb4:2 A4:2', 'G4:6 r:2',
     'C5:3 A4:1 C5:2 F5:2', 'E5:4 C5:2 A4:2', 'Bb4:2 D5:2 C5:2 Bb4:2', 'A4:6 r:2']
B = ['A5:3 G5:1 F5:2 C5:2', 'D5:4 F5:2 A5:2', 'G5:3 F5:1 D5:2 Bb4:2', 'C5:6 r:2',
     'A5:3 G5:1 F5:2 A5:2', 'C6:4 A5:2 E5:2', 'F5:2 G5:2 E5:2 C5:2', 'F5:6 r:2']

def setup(s):
    s.prog(0, 4)    # electric piano
    s.prog(1, 11)   # vibraphone
    s.prog(2, 32)   # acoustic bass
    s.prog(3, 89)   # warm pad
    for ch, v in ((0, 78), (1, 100), (2, 84), (3, 46), (9, 52)): s.cc(ch, 7, v)
    for ch, r in ((0, 50), (1, 70), (3, 80)): s.cc(ch, 91, r)
    s.cc(0, 10, 50); s.cc(1, 10, 76)

def backing(s, t0, prog, drums=True):
    for b, c in enumerate(prog):
        bt = t0 + b * 8 * E
        for k, d in ((0, 3), (3, 2), (5, 3)):
            for p in CH[c]: s.note(0, bt + k * E, d * E, n(p) + 12, 52 + (8 if k == 0 else 0))
        for p in CH[c][1:]: s.note(3, bt, 8 * E, n(p) + 12, 40)
        s.note(2, bt, 3 * E, n(ROOT[c]) + 12, 76); s.note(2, bt + 4 * E, 3 * E, n(ROOT[c]) + 19, 64)
        if drums:
            for k in range(8): s.note(9, bt + k * E, E // 2, 42, 34 if k % 2 else 44)
            s.note(9, bt + 2 * E, E, 37, 48); s.note(9, bt + 6 * E, E, 37, 48)

def bgm():
    s = Song(BPM); setup(s); t = 0
    t1 = melody(s, 1, t, A, 92, 0, .9); backing(s, t, PROG[:8], False)
    t2 = melody(s, 1, t1, B, 96, 0, .9); backing(s, t1, PROG[8:])
    t3 = melody(s, 1, t2, A, 96, 0, .9); melody(s, 0, t2, A, 50, 1, .5); backing(s, t2, PROG[:8])
    print('bgm seconds', loop_render(s, t3, BPM, f'{OUT}/bgm', 80, 0.78))

def jingles():
    s = Song(150); setup(s)   # one-piece peel!
    melody(s, 1, 0, ['C5:1 F5:1 A5:1 C6:5'], 110)
    for p in CH['F']: s.note(0, 3 * E, 5 * E, n(p) + 12, 70)
    s.note(2, 3 * E, 5 * E, n('F2'), 86)
    one_shot(s, f'{OUT}/hitokawa')
    s = Song(120); setup(s)   # result
    melody(s, 1, 0, ['A5:1 G5:1 F5:1 C5:1 D5:2 F5:4'], 104)
    for i, c in enumerate(['Bb', 'F']):
        for p in CH[c]: s.note(0, i * 4 * E, 4 * E + (2 * E if i else 0), n(p) + 12, 66)
    s.note(2, 0, 4 * E, n('Bb1'), 84); s.note(2, 4 * E, 6 * E, n('F1'), 84)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    bgm(); jingles()
