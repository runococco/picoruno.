# BGM + jingles for kingyo.html: a summer-festival (matsuri) tune, flute + shamisen + taiko + bell,
# rendered with FluidSynth / FluidR3_GM.   python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 104
# yo scale on D: D E G A B
A = ['A5:2 B5:2 D6:3 B5:1', 'A5:2 G5:2 E5:4', 'G5:1 A5:1 B5:2 A5:2 G5:2', 'E5:2 D5:2 E5:4',
     'A5:2 B5:2 D6:3 E6:1', 'D6:2 B5:2 A5:4', 'B5:1 A5:1 G5:2 E5:2 G5:2', 'A5:6 r:2']
B = ['D6:2 E6:2 D6:1 B5:1 A5:2', 'B5:2 D6:2 E6:4', 'D6:1 E6:1 D6:2 B5:2 A5:2', 'G5:2 A5:2 B5:4',
     'E6:2 D6:2 B5:2 A5:2', 'G5:2 E5:2 G5:2 A5:2', 'B5:2 A5:1 G5:1 E5:2 G5:2', 'D5:6 r:2']
ROOTS = ['D', 'G', 'E', 'D', 'D', 'G', 'E', 'A'] + ['D', 'E', 'D', 'G', 'E', 'G', 'E', 'D']

def setup(s):
    s.prog(0, 73)   # flute (stands in for the shinobue)
    s.prog(1, 106)  # shamisen
    s.prog(2, 116)  # taiko
    s.prog(3, 107)  # koto
    s.prog(4, 33)   # soft bass
    for ch, v in ((0, 104), (1, 80), (2, 96), (3, 70), (4, 64), (9, 84)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 30), (3, 60)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(3, 10, 84)

def backing(s, t0, roots, busy=1.0):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E
        # taiko: don . don don . . don .  (+ rim "ka" on the off-beats)
        for k, v in ((0, 96), (3, 70), (4, 88), (6, 64)): s.note(2, bt + k * E, E, n('C3'), v)
        for k in (2, 5, 7): s.note(9, bt + k * E, E // 2, 37, int(52 * busy))
        # atarigane-like bell: chan-chiki
        for k, v in ((0, 70), (2, 52), (3, 44), (4, 66), (6, 52), (7, 44)): s.note(9, bt + k * E, E // 2, 67, int(v * busy))
        # shamisen on the backbeat
        for k in (1, 3, 5, 7): s.note(1, bt + k * E, E // 2, n(r + '4'), 62); s.note(1, bt + k * E, E // 2, n(r + '3'), 56)
        s.note(4, bt, 4 * E, n(r + '2'), 70); s.note(4, bt + 4 * E, 4 * E, n(r + '2'), 62)

def bgm():
    s = Song(BPM); setup(s); t = 0
    t1 = melody(s, 0, t, A, 96, 0, 0.9); backing(s, t, ROOTS[:8], .8)
    t2 = melody(s, 0, t1, A, 100, 0, 0.9); melody(s, 3, t1, A, 70, -1, 0.5); backing(s, t1, ROOTS[:8])
    t3 = melody(s, 0, t2, B, 104, 0, 0.9); melody(s, 3, t2, B, 66, -1, 0.5); backing(s, t2, ROOTS[8:])
    print('bgm seconds', loop_render(s, t3, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(130); setup(s)   # time up
    melody(s, 0, 0, ['A5:1 B5:1 D6:1 E6:1 D6:2 B5:1 D6:5'], 104); melody(s, 3, 0, ['r:4 D5:6'], 70)
    for k in range(3): s.note(2, k * E, E, n('C3'), 100)
    s.note(2, 4 * E, 4 * E, n('C3'), 120); s.note(9, 4 * E, E, 67, 90)
    one_shot(s, f'{OUT}/finish')
    s = Song(150); setup(s)   # rare golden fish
    melody(s, 3, 0, ['D6:1 E6:1 G6:1 A6:1 B6:1 D7:3'], 96); melody(s, 0, 2 * E, ['B6:6'], 70)
    one_shot(s, f'{OUT}/rare')

if __name__ == '__main__':
    bgm(); jingles()
