# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D F G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| flip.mp3 | Kenney Rpg Audio | bookFlip1.ogg | unpitched / unchanged |
| press.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -0.39 semitones |
| crack.mp3 | Kenney Rpg Audio | chop.ogg | unpitched / unchanged |
| place.mp3 | Kenney Rpg Audio | bookPlace1.ogg | unpitched / unchanged |
| collect.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| brush.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| burnt.mp3 | Kenney Impact Sounds | impactSoft_heavy_000.ogg | pitched -0.84 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
