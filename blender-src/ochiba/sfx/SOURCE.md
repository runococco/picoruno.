# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| sweep1.mp3 | Kenney Impact Sounds | footstep_grass_000.ogg | unpitched / unchanged |
| sweep2.mp3 | Kenney Impact Sounds | footstep_grass_002.ogg | unpitched / unchanged |
| sweep3.mp3 | Kenney Impact Sounds | footstep_grass_004.ogg | unpitched / unchanged |
| swish.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| flutter.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| cat.mp3 | Kenney Interface Sounds | pluck_002.ogg | pitched +0.93 semitones |
| crack1.mp3 | Kenney Impact Sounds | footstep_wood_000.ogg | pitched +1.08 semitones |
| crack2.mp3 | Kenney Impact Sounds | footstep_wood_002.ogg | pitched -0.04 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |
| pile.mp3 | Kenney Impact Sounds | impactSoft_medium_000.ogg | pitched +0.79 semitones |

BGM, finish / found / ready jingles and wind gust: original (music.py), FluidSynth + FluidR3_GM (MIT).
