# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pump.mp3 | UI SFX library | rubber/swipe | pitched -0.12 semitones |
| creak.mp3 | Kenney Rpg Audio | creak1.ogg | unpitched / unchanged |
| jump.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| land.mp3 | Kenney Impact Sounds | footstep_grass_002.ogg | unpitched / unchanged |
| star.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched +1.31 semitones |
| oops.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
