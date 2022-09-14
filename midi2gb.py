from MIDI import MIDIFile, Events
from sys import argv

from gbsound import Note, Chip
import wave
import struct
import random

# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
# From: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e

def get_frequency(note, A4=440):
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    octave = int(note[2]) if len(note) == 3 else int(note[1])
        
    keyNumber = notes.index(note[0:-1]);
    
    if (keyNumber < 3) :
        keyNumber = keyNumber + 12 + ((octave - 1) * 12) + 1; 
    else:
        keyNumber = keyNumber + ((octave - 1) * 12) + 1; 

    return A4 * 2** ((keyNumber- 49) / 12)

# A programmable sound generator (PSG)
chip = Chip()




def parse(file):

    wave_file = wave.open('sounds/midi2gb.wav', "wb")
    wave_file.setnchannels(1) # Mono
    wave_file.setframerate(chip.sample_rate)
    wave_file.setsampwidth(2) # Bytes to use for samples
    
    c=MIDIFile(file)
    c.parse()
    print(str(c))

    for idx, track in enumerate(c):
        #print(f'Track {idx}:')
        #print(type(track))
        
        track.parse()
        #    pass
        for e in track:

            try:
                e.message.onOff
            except:
                pass
            else:
                if e.message.onOff == "ON":
                    f = get_frequency(str(e.message.note))
                    print("Event:",e)
                    #print("Time:", e.time)
                    #print("onOff:", e.message.onOff)
                    #print("Note", e.message.note)
                    #print("Frequency", f)
                    #print("channel:", e.channel)

                    chip.set_freg(f, 0)
                    chip.set_freg(f/2, 1)
                    chip.set_freg(f/4, 2)
                    #chip.sweep_up(bool(random.randint(0,2)))
                    #chip.envelop(True)
                    chip.trig()
                    #chip.set_freg(note.value/2, 1)
                    #chip.set_freg(note.value/4, 2)
                    for i in range(int(chip.sample_rate / 6)):
                        v = 100 * (next(chip))
                        s = struct.pack('<h', int(v))
                        wave_file.writeframesraw(s)


    wave_file.close()


 
tetris = "midi/tetris_2.mid"

parse(tetris)


"""
event_attributes: ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__',
'__ge__', '__getattr__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__',
'__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
'__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'buffer', 'build', 'channel', 'command', 'commands',
'data', 'getChunk', 'getInt', 'getVarLengthChunk', 'getVarLengthInt', 'header', 'length',
'message', 'parameters', 'stringify', 'time']

"""

"""
note:
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__',
'__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__',
'__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__',
'__subclasshook__', '__weakref__', '_fromNumber', '_fromPitchAndOctave', '_fromString',
'note', 'notes', 'number', 'octave']

"""