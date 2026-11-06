# Shared helpers: compose MIDI with mido, render with FluidSynth + FluidR3_GM (MIT soundfont), encode mp3.
import mido, subprocess, os, wave, numpy as np
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


def loop_render(song, total_ticks, bpm, out, kbps=80, peak=0.8):
    """Render a looping track; folds the reverb tail onto the start so the loop is seamless."""
    song.save(out + '.mid'); render(out + '.mid', out + '_raw.wav')
    a = read(out + '_raw.wav'); L = int(round(total_ticks / TPB * 60 / bpm * SR))
    loop = a[:L].copy(); tail = a[L:]; loop[:len(tail)] += tail[:L]
    write(normalize(loop, peak), out + '.wav'); mp3(out + '.wav', out + '.mp3', kbps)
    return L / SR

def one_shot(song, out, kbps=96, peak=0.85):
    song.save(out + '.mid'); render(out + '.mid', out + '_raw.wav')
    a = read(out + '_raw.wav')
    nz = np.where(np.abs(a).max(1) > 0.002)[0]; a = a[:nz[-1] + 1] if len(nz) else a
    f = np.linspace(1, 0, min(len(a), SR // 10)); a[-len(f):] *= f[:, None]
    write(normalize(a, peak), out + '.wav'); mp3(out + '.wav', out + '.mp3', kbps)
