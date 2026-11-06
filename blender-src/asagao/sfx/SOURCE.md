# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| turn.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| turn2.mp3 | Kenney Impact Sounds | impactWood_light_004.ogg | pitched -0.68 semitones |
| undo.mp3 | UI SFX library | soft/back | pitched -0.54 semitones |
| block.mp3 | Kenney Impact Sounds | impactSoft_medium_000.ogg | pitched +0.79 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM, bloom notes and jingles (clear / perfect): original (music.py), FluidSynth + FluidR3_GM (MIT).
