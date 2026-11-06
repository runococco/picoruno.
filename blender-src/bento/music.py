# Composes the BGM and jingles for bento.html as MIDI and renders them with FluidSynth
# using the FluidR3_GM soundfont (MIT licence, free). Output: mp3 files in <outdir>.
# python3 music.py <outdir>     (needs: pip install mido; apt install fluidsynth fluid-soundfont-gm ffmpeg)
import mido, subprocess, sys, os, wave, numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
SF = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
SR = 44100
TPB = 480
E = TPB // 2  # eighth note

NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
def n(s):
    s = s.strip(); b = NOTE[s[0]]; i = 1
    while i < len(s) and s[i] in '#b':
        b += 1 if s[i] == '#' else -1; i += 1
    return 12 * (int(s[i:]) + 1) + b

class Song:
    def __init__(self, bpm):
        self.bpm = bpm; self.ev = []   # (tick, kind, ch, a, b)
    def prog(self, ch, program):
        self.ev.append((0, 'pc', ch, program, 0))
    def cc(self, ch, c, v):
        self.ev.append((0, 'cc', ch, c, v))
    def note(self, ch, t, dur, pitch, vel):
        self.ev.append((t, 'on', ch, pitch, vel)); self.ev.append((t + dur, 'off', ch, pitch, 0))
    def save(self, path):
        mf = mido.MidiFile(ticks_per_beat=TPB); tr = mido.MidiTrack(); mf.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(self.bpm)))
        order = {'pc': 0, 'cc': 1, 'off': 2, 'on': 3}
        last = 0
        for t, k, ch, a, b in sorted(self.ev, key=lambda e: (e[0], order[e[1]])):
            d = t - last; last = t
            if k == 'pc': tr.append(mido.Message('program_change', channel=ch, program=a, time=d))
            elif k == 'cc': tr.append(mido.Message('control_change', channel=ch, control=a, value=b, time=d))
            elif k == 'on': tr.append(mido.Message('note_on', channel=ch, note=a, velocity=b, time=d))
            else: tr.append(mido.Message('note_off', channel=ch, note=a, velocity=0, time=d))
        mf.save(path)

def melody(song, ch, start, bars, vel=96, oct=0, legato=0.9):
    t = start
    for bar in bars:
        for tok in bar.split():
            name, d = tok.split(':'); d = int(d) * E
            if name != 'r':
                song.note(ch, t, int(d * legato), n(name) + 12 * oct, vel)
            t += d
    return t

CHORDS = {  # root, chord tones (closed voicing around middle C)
    'F': ('F2', ['F3', 'A3', 'C4']), 'C': ('C2', ['E3', 'G3', 'C4']), 'C/E': ('E2', ['E3', 'G3', 'C4']),
    'Dm': ('D2', ['D3', 'F3', 'A3']), 'Bb': ('Bb1', ['D3', 'F3', 'Bb3']), 'Am': ('A1', ['E3', 'A3', 'C4']),
    'Gm': ('G1', ['D3', 'G3', 'Bb3']), 'C7': ('C2', ['E3', 'G3', 'Bb3']),
}

def bar_chords(spec):
    """'F' -> [(F, 8)], 'Bb C' -> [(Bb, 4), (C, 4)] in eighths"""
    cs = spec.split(); return [(c, 8 // len(cs)) for c in cs]

def accomp(song, start, prog_bars, guitar=1, bass=2, drums=9, intensity=1.0):
    t = start; bar = 8 * E
    for bi, spec in enumerate(prog_bars):
        tt = t
        for c, d in bar_chords(spec):
            root, tones = CHORDS[c]
            # bass: root on the beat, fifth-ish bounce
            song.note(bass, tt, int(E * 1.6), n(root), 92)
            if d >= 4:
                song.note(bass, tt + 3 * E, int(E * 0.8), n(root) + 7, 70)
            if d >= 8:
                song.note(bass, tt + 4 * E, int(E * 1.6), n(root) + 12, 80)
                song.note(bass, tt + 7 * E, int(E * 0.8), n(root) + 7, 66)
            # guitar: off-beat chops
            for k in range(1, d, 2):
                for p in tones:
                    song.note(guitar, tt + k * E, int(E * 0.6), n(p) + 12, int(58 * intensity))
            tt += d * E
        # drums: soft kick 1 & 3, side stick 2 & 4, shaker eighths
        for b4 in range(4):
            bt = t + b4 * 2 * E
            if b4 % 2 == 0: song.note(drums, bt, E, 36, 80)
            else: song.note(drums, bt, E, 37, 62)
            song.note(drums, bt, E // 2, 70, 50); song.note(drums, bt + E, E // 2, 70, 34)
        t += bar
    return t

A_MEL = [
    'C5:1 F5:1 A5:2 G5:1 F5:1 C5:2',
    'D5:1 E5:1 G5:2 F5:1 E5:1 C5:2',
    'D5:1 F5:1 A5:2 C6:1 A5:1 F5:2',
    'G5:3 F5:1 D5:2 r:2',
    'C5:1 F5:1 A5:2 G5:1 F5:1 C5:2',
    'E5:1 G5:1 C6:2 Bb5:1 A5:1 G5:2',
    'F5:1 G5:1 A5:1 Bb5:1 A5:2 G5:2',
    'F5:4 r:4',
]
A_CH = ['F', 'C/E', 'Dm', 'Bb', 'F', 'C', 'Bb C', 'F']
B_MEL = [
    'D6:2 C6:1 Bb5:1 A5:2 F5:2',
    'G5:2 A5:1 Bb5:1 C6:4',
    'C6:2 Bb5:1 A5:1 G5:2 E5:2',
    'F5:2 E5:1 F5:1 A5:4',
    'Bb5:2 A5:1 G5:1 D5:2 G5:2',
    'E5:2 F5:1 G5:1 C6:4',
    'A5:1 G5:1 F5:1 A5:1 D6:2 C6:2',
    'Bb5:2 A5:1 G5:1 E5:2 r:2',
]
B_CH = ['Bb', 'C', 'Am', 'Dm', 'Gm', 'C', 'F Dm', 'Gm C7']

def setup(s):
    s.prog(0, 12)   # marimba (lead)
    s.prog(1, 24)   # nylon guitar
    s.prog(2, 32)   # acoustic bass
    s.prog(3, 9)    # glockenspiel
    s.prog(4, 45)   # pizzicato strings
    for ch, vol in ((0, 110), (1, 70), (2, 96), (3, 64), (4, 70), (9, 80)):
        s.cc(ch, 7, vol)
    s.cc(0, 91, 40); s.cc(3, 91, 60); s.cc(1, 91, 30); s.cc(4, 91, 40)
    s.cc(1, 10, 44); s.cc(4, 10, 84); s.cc(3, 10, 76)

def render(mid, wav, gain=0.5):
    subprocess.run(['fluidsynth', '-ni', '-g', str(gain), '-r', str(SR), '-F', wav, SF, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def read(wav):
    w = wave.open(wav); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768
    return a

def write(a, wav):
    a = np.clip(a, -1, 1); w = wave.open(wav, 'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()

def mp3(wav, out, kbps=96):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-codec:a', 'libmp3lame', '-b:a', f'{kbps}k', '-ac', '2', out], check=True)

def normalize(a, peak=0.89):
    m = np.abs(a).max(); return a * (peak / m) if m > 0 else a

def bgm():
    s = Song(116); setup(s)
    t = 0
    # A, A' (glock doubles), B, A'' with pizzicato counter-line
    t1 = melody(s, 0, t, A_MEL); accomp(s, t, A_CH, intensity=0.9)
    t2 = melody(s, 0, t1, A_MEL); melody(s, 3, t1, A_MEL, 70); accomp(s, t1, A_CH)
    t3 = melody(s, 0, t2, B_MEL); melody(s, 4, t2, B_MEL, 62, -1, 0.4); accomp(s, t2, B_CH)
    t4 = melody(s, 0, t3, A_MEL); melody(s, 3, t3, A_MEL, 70); accomp(s, t3, A_CH)
    s.save(f'{OUT}/bgm.mid'); render(f'{OUT}/bgm.mid', f'{OUT}/bgm_raw.wav')
    a = read(f'{OUT}/bgm_raw.wav')
    L = int(round(t4 / TPB * 60 / 116 * SR))
    loop = a[:L].copy(); tail = a[L:]
    loop[:len(tail)] += tail[:L]           # fold the reverb tail onto the start so the loop is seamless
    write(normalize(loop, 0.8), f'{OUT}/bgm.wav'); mp3(f'{OUT}/bgm.wav', f'{OUT}/bgm.mp3', 80)
    print('bgm seconds', L / SR)

def jingle(name, events, bpm=132):
    s = Song(bpm); setup(s)
    for ch, start, mel, vel, oct in events:
        melody(s, ch, start * E, [mel], vel, oct, 0.95)
    s.save(f'{OUT}/{name}.mid'); render(f'{OUT}/{name}.mid', f'{OUT}/{name}_raw.wav')
    a = read(f'{OUT}/{name}_raw.wav')
    # trim trailing silence
    nz = np.where(np.abs(a).max(1) > 0.002)[0]; a = a[:nz[-1] + 1] if len(nz) else a
    f = np.linspace(1, 0, min(len(a), SR // 10)); a[-len(f):] *= f[:, None]
    write(normalize(a, 0.85), f'{OUT}/{name}.wav'); mp3(f'{OUT}/{name}.wav', f'{OUT}/{name}.mp3', 96)

if __name__ == '__main__':
    bgm()
    # bento complete: bright rising arpeggio + chord
    jingle('clear', [
        (0, 0, 'C5:1 F5:1 A5:1 C6:3', 110, 0), (3, 0, 'C5:1 F5:1 A5:1 C6:3', 80, 0),
        (1, 3, 'F4:3', 80, 0), (1, 3, 'A4:3', 80, 0), (1, 3, 'C5:3', 80, 0), (2, 3, 'F2:3', 90, 0),
    ])
    # all five bentos done
    jingle('finish', [
        (0, 0, 'C5:1 D5:1 E5:1 G5:1 A5:2 G5:1 A5:1 C6:6', 110, 0),
        (3, 0, 'r:4 A5:2 G5:1 A5:1 C6:6', 80, 0),
        (1, 4, 'F4:2 E4:2 F4:6', 70, 0), (1, 4, 'A4:2 G4:2 A4:6', 70, 0), (1, 4, 'C5:2 C5:2 C5:6', 70, 0),
        (2, 0, 'F2:4 Bb1:2 C2:2 F2:6', 92, 0),
    ])
