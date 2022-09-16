# gbsound.py
A Python implementation of the Game Boy sound chip. This project started it's life
as a project at [Unity](https://unity.com/) Hackweek 2022.

Not all features of the Game Boy sound chip have been implemented.

## Overview

The main class is _Chip_. It has a number of channels implemented in the class _Channel_.
The channels can be manipulated via the _Chip_ object. The waveforms of the channels
are implemented in the _Waveform_ class. To control various time based features, the
channels use the _Timer_ class.

## How to use
To get sound data from the _Chip_, one has to configure it, and then request a number of samples.
The samples can be saved in a _wav_ file for later playback.

The file _midi2gba.py_ parses [MIDI](https://en.wikipedia.org/wiki/MIDI) files and outputs _wav_ files.
Listen to the [pre-rendered audio files](https://github.com/tobiasbp/gbsound/tree/main/sounds) that are
a part of this project.
They were created by parsing [these MIDI files](https://github.com/tobiasbp/gbsound/tree/main/midi).

## Example of use
Create a 1 second wav file called _test_tone.wav_ with a 440Hz note being played. 
```python
from gbsound import Chip

# The sound chip
chip = Chip("./test_tone.wav")

# Configure channel 0 to oscillate at 440Hz
chip.set_freq(440, 0)

# Start channel 0
chip.trig(0)

# Get 100 samples from the sound chip
for i in range(chip.sample_rate):
    print(next(chip))
```

## Research material
The following material has been used for research:  

* https://gbdev.gg8.se/wiki/articles/Gameboy_sound_hardware
* [Manuel Fuchs Emulating the Nintendo Game Boy Audio Hardware in Elm](https://www.youtube.com/watch?v=a52p6ji1WZs)
* [GBZ80 Assembly Lesson P21 - Sound on the Gameboy and Gameboy Color](https://www.youtube.com/watch?v=LCPLGkYJk5M)
* https://aselker.github.io/gameboy-sound-chip/
* http://www.devrs.com/gb/files/hosted/GBSOUND.txt

Based on the description [here]().

## Misc
* _gbsound.py_ needs Python 3.8 or newer.
* The library used for parsing MIDI files in _midi2gba.py_ is here: https://pypi.org/project/MIDIFile/
* Source of the MIDI files used: https://www.khinsider.com/midi/gameboy/tetris