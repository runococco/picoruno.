# BGM, croak, splash and jingles for kaeru.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 124
# A major pentatonic (A B C# E F#): a bouncy pond tune, marimba + clarinet over pizzicato and a light kit
A = ['E5:1 r:1 C#5:1 E5:1 F#5:2 E5:2', 'C#5:2 B4:2 A4:4', 'B4:1 r:1 C#5:1 E5:1 F#5:1 E5:1 C#5:2', 'B4:6 r:2',
     'E5:1 r:1 F#5:1 A5:1 F#5:2 E5:2', 'C#5:2 E5:2 F#5:4', 'E5:1 C#5:1 B4:1 A4:1 B4:2 C#5:2', 'A4:6 r:2']
B = ['A5:2 F#5:1 E5:1 F#5:2 A5:2', 'B5:4 A5:4', 'F#5:1 E5:1 C#5:1 E5:1 F#5:2 E5:2', 'C#5:6 r:2',
     'A5:2 B5:1 A5:1 F#5:2 E5:2', 'F#5:4 E5:2 C#5:2', 'B4:1 C#5:1 E5:1 F#5:1 E5:2 B4:2', 'A4:6 r:2']
ROOT = ['A', 'F#m', 'D', 'E', 'A', 'D', 'E', 'A'] * 2
CH = {'A': ['A2', 'E3', 'A3', 'C#4'], 'F#m': ['F#2', 'C#3', 'F#3', 'A3'], 'D': ['D2', 'A2', 'D3', 'F#3'], 'E': ['E2', 'B2', 'E3', 'G#3']}

def setup(s):
    s.prog(0, 12); s.prog(1, 71); s.prog(2, 45); s.prog(3, 32)   # marimba, clarinet, pizzicato, acoustic bass
    for ch, v in ((0, 92), (1, 74), (2, 70), (3, 84), (9, 56)): s.cc(ch, 7, v)
    for ch, r in ((0, 40), (1, 50), (2, 40), (3, 20), (9, 25)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]), 88)
        for k in (2, 6): s.note(3, bt + k * E, E, n(c[1]), 70)
        for k in (1, 3, 5, 7): s.note(2, bt + k * E, E, n(c[2]) + 12, 60); s.note(2, bt + k * E, E, n(c[3]) + 12, 54)
        for k in range(8):
            if k in (0, 4): s.note(9, bt + k * E, E, 36, 70)
            if k in (2, 6): s.note(9, bt + k * E, E, 38, 50)
            s.note(9, bt + k * E, E // 2, 42, 34 + (10 if k % 2 == 0 else 0))

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.6); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 E6:1 F#6:1 A6:2'] + ['r:8'] * 3 + ['r:4 C#6:1 E6:1 A6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(120); s.cc(9, 7, 120); s.cc(9, 91, 30)   # croak: long guiro, twice
    s.note(9, 0, E, 74, 110); s.note(9, int(E * 1.2), E, 74, 90)
    one_shot(s, f'{OUT}/croak')
    s = Song(120); s.prog(0, 122); s.prog(1, 117); s.cc(0, 7, 120); s.cc(0, 91, 20)   # splash: a burst of surf + a low melodic tom
    s.note(0, 0, E * 2, n('A5'), 120); s.note(1, 0, E, n('A2'), 100)
    one_shot(s, f'{OUT}/splash')
    s = Song(150); setup(s)   # a fly caught
    melody(s, 0, 0, ['A5:1 C#6:1 E6:2'], 96)
    one_shot(s, f'{OUT}/gulp')
    s = Song(150); setup(s)   # lotus bonus
    melody(s, 0, 0, ['E6:1 F#6:1 A6:1 C#7:1 E7:3'], 96)
    one_shot(s, f'{OUT}/lotus')
    s = Song(110); setup(s)   # game over
    melody(s, 1, 0, ['E5:2 C#5:2 B4:2 A4:4'], 90); melody(s, 0, 0, ['r:6 A4:1 E5:1 A5:4'], 70)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
