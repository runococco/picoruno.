# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| flip.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| roll.mp3 | Kenney Impact Sounds | footstep_wood_001.ogg | pitched -0.02 semitones |
| drop.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| good.mp3 | UI SFX library | organic/select | pitched -0.02 semitones |
| gold.mp3 | UI SFX library | organic/achievement | pitched +1.18 semitones |
| fire.mp3 | UI SFX library | soft/notification | pitched +0.80 semitones |
| bad.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| lost.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
