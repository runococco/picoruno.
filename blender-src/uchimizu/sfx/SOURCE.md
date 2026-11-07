# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| splash.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| swish.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| peep.mp3 | Kenney Interface Sounds | pluck_002.ogg | pitched +0.93 semitones |
| home.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| hot.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| wet.mp3 | UI SFX library | zen/drop | pitched -1.48 semitones |
| empty.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| gold.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
