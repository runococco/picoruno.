# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| catch.mp3 | Kenney Impact Sounds | impactSoft_medium_000.ogg | pitched +0.79 semitones |
| perfect.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched -0.02 semitones |
| drop.mp3 | Kenney Impact Sounds | impactSoft_heavy_002.ogg | pitched +0.67 semitones |
| whiff.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| add.mp3 | Kenney Interface Sounds | drop_003.ogg | pitched +1.02 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
