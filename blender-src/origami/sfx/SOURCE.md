# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E G A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pick.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| fold.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| crease.mp3 | Kenney Rpg Audio | bookPlace1.ogg | unpitched / unchanged |
| undo.mp3 | Kenney Rpg Audio | bookFlip1.ogg | unpitched / unchanged |
| nope.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| match.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| star.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
