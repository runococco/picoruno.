# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| draw.mp3 | Kenney Interface Sounds | scratch_001.ogg | unpitched / unchanged |
| erase.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| step.mp3 | UI SFX library | soft/press | pitched -0.98 semitones |
| turn.mp3 | Kenney Interface Sounds | tick_002.ogg | unpitched / unchanged |
| yum.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched +0.98 semitones |
| empty.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| no.mp3 | Kenney Interface Sounds | error_004.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
