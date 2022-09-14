from MIDI import MIDIFile, Events
from sys import argv

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

def parse(file):
    
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
                    print("Event:",e)
                    print("Time:", e.time)
                    print("onOff:", e.message.onOff)
                    print("Note", e.message.note)
                    print("Frequency", get_frequency(str(e.message.note)))
                    print("channel:", e.channel)

            #if onOff in dict(e.message):
            #    print("foo")
            #    pass 
            #if e.command == 144:
            #    print("FOO")
            """
            try:
                print("onOff:", e.message.onOff)
                print("note:", e.message.note)
                print("command:", e.command)
            except:
                pass

            if type(e) == Events.midi.MIDIEvent:
                print("onOff:", e.message.onOff)
                print("note:", e.message.note)
                print("command:", e.command)

            """
            #    print("event_command:", e.command)
            #    print("event_channel:", e.channel)
            #    #print("event_attributes:", dir(e))
            #    #break
            #    pass
 
tetris = "midi/tetris_theme_a.mid"

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