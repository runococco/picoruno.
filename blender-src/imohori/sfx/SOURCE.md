# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| grab.mp3 | UI SFX library | organic/press | pitched +0.47 semitones |
| dig.mp3 | Kenney Impact Sounds | footstep_grass_002.ogg | unpitched / unchanged |
| creak.mp3 | UI SFX library | rubber/drag-start | pitched +1.31 semitones |
| snap.mp3 | UI SFX library | organic/snap | pitched -1.10 semitones |
| plop.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -1.39 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (pop / gold / oops / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
