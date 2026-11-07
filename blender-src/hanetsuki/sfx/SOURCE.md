# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| hit.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| hit2.mp3 | Kenney Impact Sounds | impactWood_medium_001.ogg | pitched -0.22 semitones |
| drop.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched +1.21 semitones |
| ink.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| pop.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| combo.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| whoosh.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
