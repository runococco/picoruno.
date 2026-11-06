# BGM and jingles for kendama.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 132
# D major pentatonic (D E F# A B): a cheerful new-year tune, koto + shakuhachi over pizzicato, woodblock and taiko
A = ['A5:1 r:1 F#5:1 A5:1 B5:2 A5:2', 'F#5:2 E5:2 D5:4', 'E5:1 r:1 F#5:1 A5:1 B5:1 A5:1 F#5:2', 'E5:6 r:2',
     'A5:1 r:1 B5:1 D6:1 B5:2 A5:2', 'F#5:2 A5:2 B5:4', 'A5:1 F#5:1 E5:1 D5:1 E5:2 F#5:2', 'D5:6 r:2']
B = ['D6:2 B5:1 A5:1 B5:2 D6:2', 'E6:4 D6:4', 'B5:1 A5:1 F#5:1 A5:1 B5:2 A5:2', 'F#5:6 r:2',
     'D6:2 E6:1 D6:1 B5:2 A5:2', 'B5:4 A5:2 F#5:2', 'E5:1 F#5:1 A5:1 B5:1 A5:2 E5:2', 'D5:6 r:2']
ROOT = ['D', 'Bm', 'G', 'A', 'D', 'G', 'A', 'D'] * 2
CH = {'D': ['D2', 'A2', 'D3', 'F#3'], 'Bm': ['B1', 'F#2', 'B2', 'D3'], 'G': ['G1', 'D2', 'G2', 'B2'], 'A': ['A1', 'E2', 'A2', 'C#3']}

def setup(s):
    s.prog(0, 107); s.prog(1, 77); s.prog(2, 45); s.prog(3, 32)   # koto, shakuhachi, pizzicato, acoustic bass
    for ch, v in ((0, 100), (1, 70), (2, 66), (3, 84), (9, 60)): s.cc(ch, 7, v)
    for ch, r in ((0, 40), (1, 60), (2, 40), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]) + 12, 88)
        for k in (2, 6): s.note(3, bt + k * E, E, n(c[1]) + 12, 70)
        for k in (1, 3, 5, 7): s.note(2, bt + k * E, E, n(c[2]) + 12, 58); s.note(2, bt + k * E, E, n(c[3]) + 12, 52)
        for k in range(8):
            if k in (0, 3, 4): s.note(9, bt + k * E, E, 36, 72 if k != 3 else 50)   # taiko-ish kick
            if k in (2, 6): s.note(9, bt + k * E, E, 76, 62)                         # high woodblock
            if k in (1, 5, 7): s.note(9, bt + k * E, E // 2, 77, 40)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 96, 0, 0.55); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 A6:1 B6:1 D7:2'] + ['r:8'] * 3 + ['r:4 F#6:1 A6:1 D7:2'], 72); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(160); setup(s)   # a cup catch (combo jingles are made by pitching this in the game)
    melody(s, 0, 0, ['D6:1 A6:2'], 100)
    one_shot(s, f'{OUT}/ok')
    s = Song(160); setup(s)   # spike!
    melody(s, 0, 0, ['D6:1 F#6:1 A6:1 D7:3'], 104); s.note(9, 0, E, 49, 70)
    one_shot(s, f'{OUT}/spike')
    s = Song(150); setup(s)   # mission done
    melody(s, 0, 0, ['A5:1 B5:1 D6:1 E6:1 F#6:1 A6:3'], 96)
    one_shot(s, f'{OUT}/mission')
    s = Song(110); setup(s)   # end of round
    melody(s, 1, 0, ['A5:2 F#5:2 E5:2 D5:4'], 88); melody(s, 0, 0, ['r:6 D5:1 A5:1 D6:4'], 76)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
