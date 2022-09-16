from gbsound import Note, Chip
import wave
import struct

# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
# From: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e


def get_frequency(note:str, A4:int=440):
    """
    Translate notes like 'A#4' and 'B2' to a frequency in Hz.
    """
    notes: str = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    # Last character in the note is the octave
    octave: int = int(note[-1])

    # Note name is the note minus the last character (the octave)
    note_name = note[0:-1]

    # Convert the note_name to an int by looking up it's position in the 'notes' array
    note_number:int = notes.index(note_name)

    # Use octave to update the note_number to a an absolute position (In the note domain)
    if note_number < 3:
        note_number += 12 + ((octave - 1) * 12) + 1
    else:
        note_number += ((octave - 1) * 12) + 1

    # Return the frequency
    return A4 * 2 ** ((note_number - 49) / 12)


# A programmable sound generator (PSG) writing data to a wav file
chip = Chip(wav_file="./sounds/test_scales.wav")

# The channel to use on the chip
channel_no = 0

# Play scales
for octave in range(1, 7):
    for note in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
        # Configure the frequency of the channel
        chip.set_freq(get_frequency(note + str(octave)), channel_no)
        
        # Start the channel
        chip.trig(channel_no)

        # Write 0.5 seconds of audio to wav file
        for i in range(chip.sample_rate // 2):
            next(chip)
