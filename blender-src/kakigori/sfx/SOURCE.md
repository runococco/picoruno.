# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| shave.mp3 | Kenney Impact Sounds | footstep_snow_001.ogg | unpitched / unchanged |
| drip.mp3 | UI SFX library | glass/drop | pitched +0.23 semitones |
| pick.mp3 | Kenney Impact Sounds | impactGlass_light_001.ogg | pitched +0.56 semitones |
| crumble.mp3 | Kenney Impact Sounds | impactSoft_heavy_002.ogg | pitched -0.33 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (thanks / great / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
