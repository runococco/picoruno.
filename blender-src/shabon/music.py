# BGM and jingles for shabon.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 88
# F major pentatonic (F G A C D): a floaty bubble-blowing afternoon, music box and celesta over harp and soft bass
A = ['C6:2 A5:1 C6:1 D6:2 C6:2', 'A5:1 G5:1 F5:2 G5:4', 'A5:1 C6:1 D6:1 F6:1 D6:2 C6:2', 'G5:2 A5:2 C6:4',
     'D6:2 C6:1 D6:1 F6:2 D6:2', 'C6:1 A5:1 G5:2 A5:4', 'G5:1 A5:1 C6:1 A5:1 G5:2 D5:2', 'F5:6 r:2']
B = ['F6:2 D6:1 C6:1 D6:2 C6:2', 'A5:2 C6:2 D6:4', 'C6:1 D6:1 F6:1 D6:1 C6:2 A5:2', 'G5:6 r:2',
     'F6:2 D6:1 C6:1 A5:2 C6:2', 'D6:2 C6:2 A5:4', 'G5:1 A5:1 C6:1 D6:1 C6:2 G5:2', 'F5:6 r:2']
ROOT = ['F', 'Dm', 'Bb', 'C', 'F', 'Bb', 'C', 'F'] * 2
CH = {'F': ['F1', 'C2', 'F2', 'A2'], 'Dm': ['D1', 'A1', 'D2', 'F2'], 'Bb': ['A#1', 'F2', 'A#2', 'D3'], 'C': ['C2', 'G2', 'C3', 'E3']}

def setup(s):
    s.prog(0, 10); s.prog(1, 8); s.prog(2, 46); s.prog(3, 32)   # music box, celesta, harp, acoustic bass
    for ch, v in ((0, 92), (1, 66), (2, 62), (3, 78), (9, 40)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 80), (2, 60), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 3, n(c[0]) + 12, 80)
        for k in (0, 2, 4, 6): s.note(2, bt + k * E + E // 2, E, n(c[2]) + 12, 52); s.note(2, bt + (k + 1) * E, E, n(c[3]) + 12, 46)
        for k in range(8):
            if k in (2, 6): s.note(9, bt + k * E, E, 75, 44)
            if k in (0, 4): s.note(9, bt + k * E, E // 2, 69, 36)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 D6:1 E6:1 G6:2'] + ['r:8'] * 3 + ['r:4 B5:1 D6:1 G6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(140); setup(s)   # gold hoop / bonus
    melody(s, 0, 0, ['F5:1 A5:1 C6:1 F6:3'], 90); melody(s, 1, 0, ['r:2 C6:1 F6:3'], 70)
    one_shot(s, f'{OUT}/levelup')
    s = Song(100); setup(s)   # time up
    melody(s, 1, 0, ['C6:2 A5:2 G5:2 F5:4'], 84); melody(s, 0, 0, ['r:6 F5:1 C6:1 F6:4'], 72)
    one_shot(s, f'{OUT}/over')
    s = Song(140); setup(s)   # new best
    melody(s, 0, 0, ['C6:1 D6:1 F6:1 G6:1 A6:1 C7:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
