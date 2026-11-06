# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| scratch.mp3 | Kenney Interface Sounds | scratch_002.ogg | unpitched / unchanged |
| crack.mp3 | Kenney Impact Sounds | impactPlate_light_002.ogg | unpitched / unchanged |
| break.mp3 | Kenney Impact Sounds | impactPlate_heavy_001.ogg | unpitched / unchanged |
| pop.mp3 | UI SFX library | organic/snap | pitched -0.10 semitones |
| warn.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| coin.mp3 | Kenney Rpg Audio | handleCoins.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (clear / clean / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
