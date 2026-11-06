# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| tick.mp3 | Kenney Ui Audio | click3.ogg | unpitched / unchanged |
| tear.mp3 | Kenney Rpg Audio | cloth3.ogg | unpitched / unchanged |
| perfect.mp3 | Kenney Impact Sounds | impactGlass_medium_004.ogg | pitched -0.34 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

plate.mp3 and next.mp3: marimba and wood block played with FluidSynth + FluidR3_GM (MIT), see sfx.py.
