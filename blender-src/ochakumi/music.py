# BGM, jingles and the pouring loop for ochakumi.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 72
# A minor pentatonic (A C D E G): calm tea room, shakuhachi over harp
A = ['E5:4 D5:2 C5:2', 'D5:6 r:2', 'A4:2 C5:2 D5:2 E5:2', 'G5:6 r:2', 'E5:4 G5:2 E5:2', 'D5:4 C5:4', 'A4:2 C5:2 D5:2 C5:2', 'A4:8']
B = ['A5:4 G5:2 E5:2', 'G5:6 r:2', 'E5:2 G5:2 A5:2 G5:2', 'E5:6 r:2', 'D5:4 E5:2 G5:2', 'E5:4 D5:4', 'C5:2 D5:2 E5:2 D5:2', 'A4:8']
ROOT = ['A', 'F', 'C', 'G', 'A', 'F', 'D', 'E'] * 2
CH = {'A': ['A2', 'E3', 'A3', 'C4'], 'F': ['F2', 'C3', 'A3', 'C4'], 'C': ['C3', 'G3', 'C4', 'E4'], 'G': ['G2', 'D3', 'G3', 'D4'],
      'D': ['D3', 'A3', 'D4', 'E4'], 'E': ['E2', 'E3', 'G3', 'D4']}

def setup(s):
    s.prog(0, 77); s.prog(1, 46); s.prog(2, 49); s.prog(3, 107)   # shakuhachi, harp, slow strings, koto
    for ch, v in ((0, 92), (1, 84), (2, 50), (3, 64)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 60), (2, 80), (3, 60)): s.cc(ch, 91, r)
    s.cc(1, 10, 50); s.cc(3, 10, 82)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k, idx in enumerate((0, 1, 2, 3, 2, 1)): s.note(1, bt + k * E + (E if k > 3 else 0), 3 * E, n(c[idx]), 70)
        s.note(2, bt, 8 * E, n(c[1]), 50); s.note(2, bt, 8 * E, n(c[2]), 46)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 84, 0, 0.95); backing(s, 0, ROOT[:8])
    melody(s, 3, 0, ['r:8'] * 4 + ['r:6 E6:2', 'r:8', 'r:6 A5:2', 'r:8'], 60)
    t2 = melody(s, 0, t1, B, 88, 0, 0.95); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(110); setup(s)   # a round is done
    melody(s, 3, 0, ['A5:1 C6:1 D6:1 E6:1 G6:4'], 96); melody(s, 1, 0, ['A4:8'], 70)
    one_shot(s, f'{OUT}/clear')
    s = Song(90); setup(s)    # all done: a little bow
    melody(s, 0, 0, ['E5:2 G5:2 A5:6'], 90); melody(s, 3, 0, ['r:2 C6:1 D6:1 E6:1 G6:1 A6:6'], 76)
    for k, c in enumerate(['A2', 'E3', 'A3', 'C4', 'E4']): s.note(1, k * E // 2, 10 * E, n(c), 76)
    one_shot(s, f'{OUT}/finish')
    s = Song(140); s.prog(0, 9); s.cc(0, 91, 70)   # cup reached the line
    s.note(0, 0, 3 * E, n('E6'), 90); s.note(0, E // 2, 3 * E, n('A6'), 80)
    one_shot(s, f'{OUT}/just')

def pour():
    # pouring tea: a seamless loop of high, soft running water (GM "seashore" voice, pitched up)
    s = Song(120); s.prog(0, 122); s.prog(1, 122); s.cc(0, 7, 110); s.cc(1, 7, 80); s.cc(0, 91, 20)
    for k in range(4): s.note(0, k * 8 * E, 8 * E + 4, n('A6'), 100); s.note(1, k * 8 * E + 4 * E, 8 * E, n('E7'), 80)
    print('pour seconds', loop_render(s, 4 * 8 * E, 120, f'{OUT}/pour', 80, 0.7))

if __name__ == '__main__':
    bgm(); jingles(); pour()
