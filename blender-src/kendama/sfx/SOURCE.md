# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| clack.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| clack2.mp3 | Kenney Impact Sounds | impactWood_light_004.ogg | pitched -0.68 semitones |
| toss.mp3 | UI SFX library | rubber/swipe | pitched -0.12 semitones |
| miss.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (ok / spike / mission / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
