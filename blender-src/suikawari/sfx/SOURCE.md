# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| step.mp3 | Kenney Impact Sounds | footstep_snow_002.ogg | unpitched / unchanged |
| swish.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| crack.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| thud.mp3 | Kenney Impact Sounds | impactSoft_heavy_001.ogg | pitched +0.67 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| spin.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (perfect / nice / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
