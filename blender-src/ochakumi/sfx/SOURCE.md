# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (A C D E G) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| drip.mp3 | UI SFX library | zen/drop | pitched -1.48 semitones |
| plop.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| spill.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -0.39 semitones |
| pick.mp3 | Kenney Impact Sounds | impactPlate_light_000.ogg | unpitched / unchanged |
| set.mp3 | Kenney Impact Sounds | impactPlate_light_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM, jingles (clear / finish / just) and the pouring loop: original (music.py), FluidSynth + FluidR3_GM (MIT).
