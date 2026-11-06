# BGM, jingles and the sizzle loop for taiyaki.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 118
# G major pentatonic (G A B D E): a busy little street stall, shamisen + koto over taiko and wood blocks
A = ['D5:1 E5:1 G5:2 E5:1 D5:1 B4:2', 'D5:2 E5:2 G5:4', 'A5:1 G5:1 E5:2 D5:1 E5:1 G5:2', 'E5:2 D5:2 B4:4',
     'G4:1 A4:1 B4:2 D5:1 B4:1 A4:2', 'B4:2 D5:2 E5:4', 'G5:1 E5:1 D5:2 E5:1 D5:1 B4:2', 'A4:2 B4:2 G4:4']
B = ['B5:2 A5:1 G5:1 A5:2 B5:2', 'D6:4 B5:4', 'A5:1 B5:1 A5:1 G5:1 E5:2 G5:2', 'A5:6 r:2',
     'G5:2 E5:1 D5:1 E5:2 G5:2', 'B5:4 A5:4', 'G5:1 A5:1 G5:1 E5:1 D5:2 E5:2', 'G5:6 r:2']
ROOT = ['G', 'G', 'C', 'G', 'Em', 'C', 'D', 'G'] * 2
CH = {'G': ['G2', 'D3', 'G3', 'B3'], 'C': ['C3', 'G3', 'C4', 'E4'], 'Em': ['E2', 'B2', 'E3', 'G3'], 'D': ['D2', 'A2', 'D3', 'F#3']}

def setup(s):
    s.prog(0, 106); s.prog(1, 107); s.prog(2, 116); s.prog(3, 33)   # shamisen, koto, taiko, bass
    for ch, v in ((0, 96), (1, 70), (2, 80), (3, 84), (9, 60)): s.cc(ch, 7, v)
    for ch, r in ((0, 40), (1, 50), (2, 30), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        s.note(3, bt, E * 2, n(c[0]), 90); s.note(3, bt + 3 * E, E, n(c[1]), 70); s.note(3, bt + 4 * E, E * 2, n(c[0]), 84); s.note(3, bt + 7 * E, E, n(c[1]), 66)
        for k in (1, 3, 5, 7): s.note(1, bt + k * E, E, n(c[2]) + 12, 52); s.note(1, bt + k * E, E, n(c[3]) + 12, 48)
        s.note(2, bt, E, n('C3'), 96); s.note(2, bt + 3 * E, E, n('C3'), 70); s.note(2, bt + 4 * E, E, n('C3'), 86)
        for k in range(8): s.note(9, bt + k * E, E // 2, 76 if k % 2 == 0 else 77, 60 if k % 4 == 0 else 40)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.7); backing(s, 0, ROOT[:8])
    t2 = melody(s, 0, t1, B, 94, 0, 0.7); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def jingles():
    s = Song(160); setup(s)   # a happy customer
    melody(s, 1, 0, ['G5:1 B5:1 D6:1 G6:3'], 92); melody(s, 0, 0, ['r:2 D5:1 G5:3'], 80)
    one_shot(s, f'{OUT}/happy')
    s = Song(150); setup(s)   # perfect golden fish
    melody(s, 1, 0, ['D6:1 E6:1 G6:1 A6:1 B6:1 D7:3'], 96); s.note(2, 0, E, n('C3'), 100); s.note(2, 5 * E, E, n('C3'), 100)
    one_shot(s, f'{OUT}/perfect')
    s = Song(100); setup(s)   # a customer gives up
    melody(s, 0, 0, ['E5:1 D5:1 B4:3'], 80)
    one_shot(s, f'{OUT}/sad')
    s = Song(110); setup(s)   # closing time
    melody(s, 0, 0, ['B4:1 D5:1 E5:1 G5:5'], 96); melody(s, 1, 0, ['r:1 G5:1 B5:1 D6:5'], 76)
    s.note(2, 0, E, n('C3'), 100); s.note(2, 2 * E, E, n('C3'), 100); s.note(2, 3 * E, E * 2, n('C3'), 110)
    one_shot(s, f'{OUT}/finish')

def sizzle():
    # oil sizzle under the iron: GM "seashore" voice, short, pitched up; a seamless loop
    s = Song(120); s.prog(0, 122); s.prog(1, 122); s.cc(0, 7, 110); s.cc(1, 7, 80); s.cc(0, 91, 10)
    for k in range(4): s.note(0, k * 8 * E, 8 * E + 4, n('C7'), 100); s.note(1, k * 8 * E + 4 * E, 8 * E, n('G7'), 80)
    print('sizzle seconds', loop_render(s, 4 * 8 * E, 120, f'{OUT}/sizzle', 80, 0.7))

if __name__ == '__main__':
    bgm(); jingles(); sizzle()
