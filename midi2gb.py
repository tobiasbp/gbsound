from MIDI import MIDIFile, Events
from sys import argv
from pathlib import Path
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




def parse(file_midi, file_wav, bpm = 120, transpose = 1.0):
    """
    Higher number for speed , is slower tempo.
    """
    print(f"Converting {file_midi} to {file_wav}")
    #file_midi = f"midi/{file_name}.mid"
    #file_wav = f"sounds/{file_name}.wav"
    assert file_midi != file_wav

    c=MIDIFile(file_midi)
    c.parse()
    print(str(c))

    # If < 2^15 it's ticks pr quarter node
    ticks_pr_quarter_node = c.division
    assert ticks_pr_quarter_node < 2**15, "Only 15 bit division values supported"

    #ticks_pr_second = (60 / bpm) * (4 * ticks_pr_quarter_node)
    ticks_pr_second = (bpm * 4 * ticks_pr_quarter_node) / 60
    samples_pr_tick = int(44100 // ticks_pr_second)
    print("BPM:", bpm)
    print("Ticks pr quarter node:", ticks_pr_quarter_node)
    print("Ticks pr second:", ticks_pr_second)
    print("Samples pr. tick:", samples_pr_tick)

    # FIXME: This number is way off!
    assert (44100 - 5000) <= (v := ticks_pr_second * samples_pr_tick) <= (44100 + 5000), f"Samples pr second: {v}"
    print("Calculated sampler pr. second (target: 44100):", v)
    
    wave_file = wave.open(file_wav, "wb")
    wave_file.setnchannels(1) # Mono
    wave_file.setframerate(chip.sample_rate)
    wave_file.setsampwidth(2) # Bytes to use for samples
    

    prev_event_time = 0
    event_no = 0
    no_of_channels = 3

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
                    f = int(f * transpose)
                    this_event_time = e.time
                    event_time_diff = this_event_time - prev_event_time
                    #print("Diff:", event_time_diff)
                    prev_event_time = this_event_time
                    #print("Event:",e)
                    #print("Tempo:",e.tempo)
                    #print("Time:", e.time)
                    #print("onOff:", e.message.onOff)
                    #print("Note", e.message.note)
                    #print("Frequency", f)
                    #print("MIDI channel:", e.channel)

                    if event_no > 0:
                        # Get samples since last event
                        #for i in range((event_time_diff // ticks_pr_quarter_node) * 1):
                        for i in range(samples_pr_tick * event_time_diff):
                            v = next(chip)
                            s = struct.pack('<h', int(v))
                            wave_file.writeframesraw(s)

                    channel_no = event_no % no_of_channels
                    #print("GB channel:", channel_no)
                    chip.set_freg(f, channel_no)
                    #chip.sweep_enable(bool(random.randint(0,2)), channel_no)
                    #chip.envelope_add(bool(random.randint(0,2)), channel_no)
                    
                    chip.set_freg(f/2, channel_no + 1)
                    #chip.set_freg(f/4, 2)
                    chip.trig(channel_no)
                    #chip.trig(channel_no + 1)


                    event_no += 1

    wave_file.close()
    print(f"file://{Path(file_wav).resolve()}" )
    print()


#parse("./midi/tetris_2.mid", "./sounds/tetris_2.wav", bpm = 30)
#parse("./midi/music-a-cool-remix-.mid", "./sounds/music-a-cool-remix-.wav", bpm = 60)
#parse("./midi/tetris_remix.mid", "./sounds/tetris_remix.wav", bpm = 60)
#parse("./midi/daisy-s-theme.mid", "./sounds/daisy-s-theme.wav", bpm = 60, transpose=0.5)
#parse("./midi/megaman-end.mid", "./sounds/megaman-end.wav", bpm = 60, transpose=0.5)
parse("./midi/SMB3_hammer.mid", "./sounds/SMB3_hammer.wav", bpm = 120, transpose=1.0)

#for f in Path("./midi").glob("*.mid"):
#    file_midi = f
#    file_wav = Path("./sounds/" + f.stem + ".wav")
#    parse(str(file_midi), str(file_wav))
