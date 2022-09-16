from gbsound import Note, Chip
import wave
import struct

# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
# From: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e


def get_frequency(note, A4=440):
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    octave = int(note[2]) if len(note) == 3 else int(note[1])

    keyNumber = notes.index(note[0:-1])

    if keyNumber < 3:
        keyNumber = keyNumber + 12 + ((octave - 1) * 12) + 1
    else:
        keyNumber = keyNumber + ((octave - 1) * 12) + 1

    return A4 * 2 ** ((keyNumber - 49) / 12)


# A programmable sound generator (PSG)
chip = Chip(wav_file="./sounds/test_scales.wav")

# Play scales
channel_no = 0

for octave in range(1, 7):
    for note in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
        # Configure chip
        chip.set_freq(get_frequency(note + str(octave)), channel_no)
        chip.trig(channel_no)

        # Write 0.5 seconds of audio to file
        for i in range(chip.sample_rate // 2):
            next(chip)
