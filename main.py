
from gbsound import Note, Chip
import wave
import struct

tetris_theme = [
    #(Note.A, 1.0),
    (Note.E, 1.0),
    (Note.B, 0.5),
    (Note.C, 0.5),

    (Note.D, 1.0),
    (Note.C, 0.5),
    (Note.B, 0.5),

    (Note.A, 1.0),
    (Note.A, 0.5),
    (Note.C, 0.5),

    (Note.E, 1.0),
    (Note.D, 0.5),
    (Note.C, 0.5),
     
    (Note.B, 2.0),
]

# A programmable sound generator (PSG)
chip = Chip()

wave_file = wave.open('test.wav', "wb")
wave_file.setnchannels(1) # Mono
wave_file.setframerate(chip.sample_rate)
wave_file.setsampwidth(2) # Bytes to use for samples

"""
for i in range(chip.sample_rate):
    v = 100 * (next(chip))
    s = struct.pack('<h', int(v))
    wave_file.writeframesraw(s)
"""

for note, length in tetris_theme:
    chip.set_freg(note.value, 0)
    chip.set_freg(note.value/2, 1)
    chip.set_freg(note.value/4, 2)
    chip.trig()
    for i in range(int(chip.sample_rate * length * 1/3)):
        v = 100 * (next(chip))
        s = struct.pack('<h', int(v))
        wave_file.writeframesraw(s)

wave_file.close()
