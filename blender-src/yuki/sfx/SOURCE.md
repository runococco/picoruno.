# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| crunch1.mp3 | Kenney Impact Sounds | footstep_snow_000.ogg | unpitched / unchanged |
| crunch2.mp3 | Kenney Impact Sounds | footstep_snow_002.ogg | unpitched / unchanged |
| crunch3.mp3 | Kenney Impact Sounds | footstep_snow_004.ogg | unpitched / unchanged |
| bump.mp3 | Kenney Impact Sounds | impactSoft_heavy_001.ogg | pitched +0.67 semitones |
| stack.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched -0.79 semitones |
| pop.mp3 | UI SFX library | soft/drop | pitched -1.49 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (done / perfect / finish): original (music.py), FluidSynth + FluidR3_GM (MIT).
