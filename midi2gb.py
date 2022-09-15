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
    notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    octave = int(note[2]) if len(note) == 3 else int(note[1])

    keyNumber = notes.index(note[0:-1])

    if keyNumber < 3:
        keyNumber = keyNumber + 12 + ((octave - 1) * 12) + 1
    else:
        keyNumber = keyNumber + ((octave - 1) * 12) + 1

    return A4 * 2 ** ((keyNumber - 49) / 12)


def parse(file_midi, file_wav, bpm=120, transpose=1.0, chip=Chip()):
    """
    Higher number for speed , is slower tempo.
    """
    print(f"Converting {file_midi} to {file_wav}")
    # file_midi = f"midi/{file_name}.mid"
    # file_wav = f"sounds/{file_name}.wav"
    assert file_midi != file_wav

    c = MIDIFile(file_midi)
    c.parse()
    print(str(c))

    # If < 2^15 it's ticks pr quarter node
    ticks_pr_quarter_node = c.division
    assert ticks_pr_quarter_node < 2**15, "Only 15 bit division values supported"

    # ticks_pr_second = (60 / bpm) * (4 * ticks_pr_quarter_node)
    ticks_pr_second = (bpm * 4 * ticks_pr_quarter_node) / 60
    samples_pr_tick = int(44100 // ticks_pr_second)
    print("BPM:", bpm)
    print("Ticks pr quarter node:", ticks_pr_quarter_node)
    print("Ticks pr second:", ticks_pr_second)
    print("Samples pr. tick:", samples_pr_tick)

    # FIXME: This number is way off!
    assert (
        (44100 - 5000) <= (v := ticks_pr_second * samples_pr_tick) <= (44100 + 5000)
    ), f"Samples pr second: {v}"
    print("Calculated sampler pr. second (target: 44100):", v)

    wave_file = wave.open(file_wav, "wb")
    wave_file.setnchannels(1)  # Mono
    wave_file.setframerate(chip.sample_rate)
    wave_file.setsampwidth(2)  # Bytes to use for samples

    prev_event_time = 0
    event_no = 0
    no_of_channels = 3

    note_on_events = []
    for track_no, track in enumerate(c):
        print(f"Track {track_no}:")
        print(str(track))

        track.parse()

        no_of_note_ons_in_track = 0
        #    pass
        for e in track:
            try:
                e.message.onOff
            except:
                pass
            else:
                if e.message.onOff == "ON":
                    no_of_note_ons_in_track += 1

                    f = get_frequency(str(e.message.note))
                    f = int(f * transpose)
                    this_event_time = e.time
                    event_time_diff = this_event_time - prev_event_time
                    # print("Diff:", event_time_diff)
                    prev_event_time = this_event_time
                    # print("Event:",e)
                    # print("Tempo:",e.tempo)
                    # print("Track:", track_no)
                    # print("Time:", e.time)
                    # print("onOff:", e.message.onOff)
                    # print("Note", e.message.note)
                    # print("Frequency", f)
                    # print("MIDI channel:", e.channel)
                    note_on_events.append(e)
                    """
                    if event_no > 0:
                        # Get samples since last event
                        #for i in range((event_time_diff // ticks_pr_quarter_node) * 1):
                        for i in range(samples_pr_tick * event_time_diff):
                            v = next(chip)
                            s = struct.pack('<h', int(v))
                            wave_file.writeframesraw(s)
                    """

                    channel_no = event_no % no_of_channels
                    # print("GB channel:", channel_no)
                    chip.set_freq(f, channel_no)
                    # chip.sweep_enable(bool(random.randint(0,2)), channel_no)
                    # chip.envelope_add(bool(random.randint(0,2)), channel_no)

                    chip.set_freq(f / 2, channel_no + 1)
                    chip.trig(channel_no)

                    event_no += 1

        print(f"Notes in track {track_no}: {no_of_note_ons_in_track}")

    print(f"Number of notes in song: {len(note_on_events)}")

    # Sort the note events on time
    sorted_events = sorted([e for e in note_on_events], key=lambda x: x.time)

    # Add a fake note at the end of the list to allow
    # the last real note to be played
    end_note = sorted_events[-1]
    # A second to allow the last real note to ring out
    end_note.time += int(ticks_pr_second)
    sorted_events.append(end_note)

    # FIXME: Does not play the last note
    for i in range(len(sorted_events) - 1):
        e_now = sorted_events[i]
        e_next = sorted_events[i + 1]
        chip_channel = i % no_of_channels
        f = get_frequency(str(e_now.message.note))
        # chip.set_freq(, chip_channel)
        chip.set_freq(int(f * transpose), chip_channel)
        chip.trig(chip_channel)
        for i in range((e_next.time - e_now.time) * samples_pr_tick):
            v = next(chip)
            s = struct.pack("<h", int(v))
            wave_file.writeframesraw(s)

    wave_file.close()

    print(f"file://{Path(file_wav).resolve()}")
    print()


c = Chip()
c.set_envelope_period(2)
parse("./midi/tetris_2.mid", "./sounds/tetris_2.wav", bpm=30, chip=c)
parse(
    "./midi/music-a-cool-remix-.mid", "./sounds/music-a-cool-remix-.wav", bpm=40, chip=c
)
# This uses a lot of channels, so you should use a chip with more channels (Unlike the real game boy)
parse("./midi/tetris_remix.mid", "./sounds/tetris_remix.wav", bpm=30, chip=c)
parse("./midi/daisy-s-theme.mid", "./sounds/daisy-s-theme.wav", bpm=60, chip=c)
parse("./midi/megaman-end.mid", "./sounds/megaman-end.wav", bpm=60, chip=c)

c.sweep_enable()
parse(
    "./midi/SMB3_hammer.mid", "./sounds/SMB3_hammer.wav", bpm=120, transpose=1.0, chip=c
)

# for f in Path("./midi").glob("*.mid"):
#    file_midi = f
#    file_wav = Path("./sounds/" + f.stem + ".wav")
#    parse(str(file_midi), str(file_wav))
