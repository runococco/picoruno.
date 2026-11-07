# BGM and jingles for amamori.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 112
# F pentatonic, a bouncy rainy-day tune: marimba lead, kalimba answers, pizzicato and bass underneath
A = ['C6:1 A5:1 C6:2 D6:2 C6:2', 'A5:1 G5:1 F5:2 G5:4', 'A5:2 C6:2 D6:1 C6:1 A5:2', 'G5:6 r:2',
     'C6:1 A5:1 C6:2 F6:2 D6:2', 'C6:1 A5:1 G5:2 A5:4', 'G5:2 A5:1 G5:1 D5:2 G5:2', 'F5:6 r:2']
B = ['F5:2 A5:2 G5:2 F5:2', 'D5:2 F5:2 G5:4', 'A5:2 C6:2 A5:2 G5:2', 'A5:6 r:2',
     'D6:2 C6:2 A5:2 C6:2', 'D6:2 F6:2 D6:4', 'C6:2 A5:2 G5:2 A5:2', 'F5:6 r:2']
ROOT = ['F', 'D', 'F', 'C', 'F', 'D', 'G', 'C'] * 2
CH = {'F': ['F2', 'C3', 'F3', 'A3'], 'D': ['D2', 'A2', 'D3', 'F3'], 'C': ['C2', 'G2', 'C3', 'G3'], 'G': ['G1', 'D2', 'G2', 'D3']}

def setup(s):
    s.prog(0, 12); s.prog(1, 108); s.prog(2, 45); s.prog(3, 32)   # marimba, kalimba, pizzicato strings, acoustic bass
    for ch, v in ((0, 96), (1, 48), (2, 64), (3, 76), (9, 44)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 60), (2, 40), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]) + 12, 80)
        arp = [c[1], c[2], c[3], c[2]]
        for k in range(8): s.note(2, bt + k * E, E * 2, n(arp[k % 4]) + 12, 50 if k % 2 else 58)
        for k in (2, 6): s.note(9, bt + k * E, E // 2, 75, 30)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 A5:1 C6:1 A5:2'] + ['r:8'] * 3 + ['r:4 G5:1 A5:1 F5:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(140); setup(s)   # level up
    melody(s, 2, 0, ['F5:1 A5:1 C6:1 F6:3'], 90); melody(s, 1, 0, ['r:2 C6:1 F6:3'], 64)
    one_shot(s, f'{OUT}/levelup')
    s = Song(100); setup(s)   # game over
    melody(s, 2, 0, ['C6:2 A5:2 G5:2 F5:4'], 84); melody(s, 1, 0, ['r:6 A4:1 G4:1 F4:4'], 64)
    one_shot(s, f'{OUT}/over')
    s = Song(140); setup(s)   # new best
    melody(s, 2, 0, ['F5:1 G5:1 A5:1 C6:1 D6:1 F6:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
