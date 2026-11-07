# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pour.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| grow.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| done.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| sticky.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| clump.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched +1.21 semitones |
| waste.mp3 | UI SFX library | soft/drop | pitched +0.51 semitones |
| batch.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
