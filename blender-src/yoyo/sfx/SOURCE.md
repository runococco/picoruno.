# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| dip.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched +1.21 semitones |
| catch.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| boing.mp3 | Kenney Interface Sounds | pluck_002.ogg | pitched +0.93 semitones |
| snap.mp3 | Kenney Rpg Audio | clothBelt2.ogg | unpitched / unchanged |
| miss.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| new.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| gold.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
