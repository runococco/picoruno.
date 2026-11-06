# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| step.mp3 | Kenney Impact Sounds | footstep_grass_002.ogg | unpitched / unchanged |
| turn.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| caught.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| touch.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched +0.98 semitones |
| mora.mp3 | Kenney Interface Sounds | pluck_002.ogg | pitched -1.07 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (win / lose / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
