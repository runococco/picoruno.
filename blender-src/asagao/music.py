# BGM, bloom notes and jingles for asagao.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 90
# C major pentatonic (C D E G A): a fresh summer morning, ocarina over nylon guitar and glockenspiel
A = ['E5:3 G5:1 A5:2 G5:2', 'E5:4 D5:2 C5:2', 'D5:3 E5:1 G5:2 E5:2', 'D5:6 r:2',
     'C5:3 D5:1 E5:2 G5:2', 'A5:4 G5:2 E5:2', 'G5:3 E5:1 D5:2 C5:2', 'C5:6 r:2']
B = ['A5:3 C6:1 A5:2 G5:2', 'E5:4 G5:4', 'A5:3 G5:1 E5:2 D5:2', 'E5:6 r:2',
     'G5:3 A5:1 C6:2 A5:2', 'G5:4 E5:2 D5:2', 'E5:3 D5:1 C5:2 D5:2', 'C5:6 r:2']
ROOT = ['C', 'Am', 'F', 'G', 'C', 'F', 'G', 'C', 'F', 'C', 'Dm', 'G', 'C', 'Am', 'G', 'C']
CH = {'C': ['C3', 'G3', 'C4', 'E4'], 'Am': ['A2', 'E3', 'A3', 'C4'], 'F': ['F2', 'C3', 'F3', 'A3'], 'G': ['G2', 'D3', 'G3', 'B3'], 'Dm': ['D3', 'A3', 'D4', 'F4']}

def setup(s):
    s.prog(0, 79); s.prog(1, 24); s.prog(2, 9); s.prog(3, 32)   # ocarina, nylon guitar, glockenspiel, acoustic bass
    for ch, v in ((0, 88), (1, 76), (2, 56), (3, 80)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 50), (2, 70), (3, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 50); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        s.note(3, bt, 3 * E, n(c[0]), 84); s.note(3, bt + 4 * E, 3 * E, n(c[1]) - 12, 70)
        for k, idx in enumerate((0, 2, 1, 3, 2, 1, 3, 2)): s.note(1, bt + k * E, int(E * 1.6), n(c[idx]), 62 if k % 2 else 72)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 86, 0, 0.92); backing(s, 0, ROOT[:8])
    melody(s, 2, 0, ['r:7 G6:1', 'r:8', 'r:7 E6:1', 'r:8'] * 2, 50)
    t2 = melody(s, 0, t1, B, 88, 0, 0.92); backing(s, t1, ROOT[8:])
    melody(s, 2, t1, ['r:6 C7:1 A6:1', 'r:8'] * 4, 48)
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.8))

def blooms():
    for k, p in enumerate(['C6', 'D6', 'E6', 'G6', 'A6', 'C7']):
        s = Song(120); s.prog(0, 9); s.prog(1, 46); s.cc(0, 91, 70); s.cc(1, 91, 70)
        s.note(0, 0, 4 * E, n(p), 90); s.note(1, 0, 4 * E, n(p) - 12, 60)
        one_shot(s, f'{OUT}/bloom{k}')

def jingles():
    s = Song(140); setup(s)   # garden cleared
    melody(s, 2, 0, ['C6:1 E6:1 G6:1 C7:4'], 92); melody(s, 0, 0, ['r:2 G5:1 C6:4'], 84)
    for k, c in enumerate(['C3', 'G3', 'C4', 'E4']): s.note(1, k * E // 2, 6 * E, n(c), 72)
    one_shot(s, f'{OUT}/clear')
    s = Song(150); setup(s)   # perfect (par)
    melody(s, 2, 0, ['G6:1 A6:1 C7:1 D7:1 E7:1 G7:4'], 92)
    one_shot(s, f'{OUT}/perfect')

if __name__ == '__main__':
    bgm(); blooms(); jingles()
