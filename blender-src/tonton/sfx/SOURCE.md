# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E G A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| ton.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| ton2.mp3 | Kenney Impact Sounds | impactWood_light_003.ogg | pitched -0.82 semitones |
| clash.mp3 | Kenney Impact Sounds | impactSoft_medium_000.ogg | pitched +0.79 semitones |
| fall.mp3 | Kenney Rpg Audio | bookPlace1.ogg | unpitched / unchanged |
| out.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| hakkeyoi.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (win / lose / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
