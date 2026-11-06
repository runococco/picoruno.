# BGM + jingles for kamihikouki.html: a breezy ocarina + guitar tune rendered with FluidSynth / FluidR3_GM.
# python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import gm
from gm import Song, melody, n, E, accomp, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 126
gm.CHORDS.update({
    'G': ('G1', ['D3', 'G3', 'B3']), 'D': ('D2', ['D3', 'F#3', 'A3']), 'Em': ('E2', ['E3', 'G3', 'B3']),
    'Bm': ('B1', ['D3', 'F#3', 'B3']), 'Am': ('A1', ['E3', 'A3', 'C4']), 'C': ('C2', ['E3', 'G3', 'C4']),
})
A_CH = ['G', 'D', 'Em', 'C', 'G', 'D', 'C D', 'G']
A = ['D5:1 G5:1 B5:2 A5:1 G5:1 D5:2', 'F#5:1 A5:1 D6:2 C6:1 A5:1 F#5:2', 'E5:1 G5:1 B5:2 D6:1 B5:1 G5:2', 'A5:3 G5:1 E5:2 r:2',
     'D5:1 G5:1 B5:2 A5:1 G5:1 D5:2', 'F#5:1 A5:1 D6:2 E6:1 D6:1 A5:2', 'C6:2 B5:1 A5:1 B5:2 A5:2', 'G5:4 r:4']
B_CH = ['C', 'D', 'Bm', 'Em', 'Am', 'D', 'G', 'D']
B = ['E6:2 D6:1 C6:1 G5:2 E5:2', 'F#5:2 A5:1 D6:1 C6:4', 'B5:2 A5:1 F#5:1 D5:2 F#5:2', 'G5:2 F#5:1 G5:1 B5:4',
     'C6:2 B5:1 A5:1 E5:2 A5:2', 'F#5:2 G5:1 A5:1 D6:4', 'B5:1 A5:1 G5:1 B5:1 D6:2 B5:2', 'A5:2 B5:1 C6:1 A5:2 r:2']

def setup(s):
    s.prog(0, 79)   # ocarina
    s.prog(1, 25)   # steel guitar
    s.prog(2, 32)   # acoustic bass
    s.prog(3, 9)    # glockenspiel
    s.prog(4, 73)   # flute
    for ch, v in ((0, 112), (1, 70), (2, 96), (3, 60), (4, 74), (9, 76)): s.cc(ch, 7, v)
    for ch, r in ((0, 50), (1, 30), (3, 60), (4, 50)): s.cc(ch, 91, r)
    s.cc(1, 10, 40); s.cc(3, 10, 84); s.cc(4, 10, 84)

def tamb(s, t0, bars):
    for b in range(bars):
        for k in range(4):
            s.note(9, t0 + b * 8 * E + (2 * k + 1) * E, E // 2, 54, 46)

def bgm():
    s = Song(BPM); setup(s); t = 0
    t1 = melody(s, 0, t, A, 100, 0, 0.85); accomp(s, t, A_CH, intensity=0.9)
    t2 = melody(s, 0, t1, A, 100, 0, 0.85); melody(s, 3, t1, A, 64, 0, 0.5); accomp(s, t1, A_CH); tamb(s, t1, 8)
    t3 = melody(s, 4, t2, B, 96, 0, 0.9); accomp(s, t2, B_CH); tamb(s, t2, 8)
    t4 = melody(s, 0, t3, A, 104, 0, 0.85); melody(s, 4, t3, A, 60, -1, 0.85); accomp(s, t3, A_CH); tamb(s, t3, 8)
    print('bgm seconds', loop_render(s, t4, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(140); setup(s)   # game over: a gentle landing phrase
    melody(s, 0, 0, ['B5:1 A5:1 G5:1 D5:1 E5:2 G5:4'], 100)
    for i, c in enumerate(['C', 'G']):
        for p in gm.CHORDS[c][1]: s.note(1, i * 2 * E + (0 if i == 0 else 2 * E), 4 * E, n(p) + 12, 64)
    s.note(2, 0, 4 * E, n('C2'), 86); s.note(2, 4 * E, 6 * E, n('G1'), 86)
    one_shot(s, f'{OUT}/land')
    s = Song(150); setup(s)   # new best
    melody(s, 0, 0, ['G5:1 B5:1 D6:1 G6:5'], 106); melody(s, 3, 0, ['G5:1 B5:1 D6:1 G6:5'], 70)
    for p in gm.CHORDS['G'][1]: s.note(1, 3 * E, 5 * E, n(p) + 12, 70)
    s.note(2, 3 * E, 5 * E, n('G1'), 90)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); jingles()
