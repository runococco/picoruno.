# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (E F# G# B C#) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| roll.mp3 | UI SFX library | rubber/swipe | pitched -0.12 semitones |
| bump.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched +0.21 semitones |
| drop.mp3 | Kenney Impact Sounds | impactSoft_heavy_002.ogg | pitched -0.33 semitones |
| paw.mp3 | UI SFX library | soft/press | pitched +0.02 semitones |
| blow.mp3 | UI SFX library | dreamy/swipe | pitched -0.43 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched -0.98 semitones |

BGM and jingles (point / win / lose / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
