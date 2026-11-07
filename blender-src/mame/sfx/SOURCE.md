# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| grab.mp3 | Kenney Interface Sounds | click_002.ogg | unpitched / unchanged |
| drop.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| in.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched +0.98 semitones |
| slip.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| roll.mp3 | Kenney Impact Sounds | impactPlate_light_001.ogg | unpitched / unchanged |
| gold.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
