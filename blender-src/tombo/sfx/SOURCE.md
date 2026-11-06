# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| flee.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| flee2.mp3 | Kenney Rpg Audio | cloth3.ogg | unpitched / unchanged |
| swish.mp3 | UI SFX library | soft/swipe | pitched -0.33 semitones |
| cage.mp3 | Kenney Rpg Audio | bookClose.ogg | unpitched / unchanged |
| land.mp3 | UI SFX library | soft/drop | pitched +0.51 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (catch / dizzy / rare / finish): original (music.py), FluidSynth + FluidR3_GM (MIT).
