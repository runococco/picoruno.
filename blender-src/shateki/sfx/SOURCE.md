# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| shoot.mp3 | UI SFX library | organic/release | pitched +0.78 semitones |
| hit.mp3 | Kenney Impact Sounds | impactPlank_medium_000.ogg | pitched +1.20 semitones |
| thud.mp3 | Kenney Impact Sounds | impactSoft_heavy_001.ogg | pitched +0.67 semitones |
| cloth.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| load.mp3 | Kenney Interface Sounds | click_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (get / gold / last / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
