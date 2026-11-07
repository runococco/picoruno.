# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E G A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| twist.mp3 | Kenney Rpg Audio | creak1.ogg | unpitched / unchanged |
| pick.mp3 | UI SFX library | organic/select | pitched -0.02 semitones |
| sweet.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| shibui.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| drop.mp3 | Kenney Impact Sounds | footstep_carpet_001.ogg | unpitched / unchanged |
| splat.mp3 | Kenney Impact Sounds | footstep_carpet_003.ogg | unpitched / unchanged |
| crow.mp3 | Kenney Rpg Audio | cloth3.ogg | unpitched / unchanged |
| shoo.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| steal.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
