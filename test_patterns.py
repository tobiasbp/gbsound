from gbsound import Chip

# A programmable sound generator (PSG) writing data to a wav file
chip = Chip(wav_file="./sounds/test_scales.wav")

# The channel to use on the chip
channel_no = 0

# Play scales
for octave in range(1, 6):
    for note in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
        # Configure the note of the channel
        chip.set_note(note + str(octave), channel_no)
        
        # Start the channel
        chip.trig(channel_no)

        # Write 0.5 seconds of audio to wav file
        for i in range(chip.sample_rate // 2):
            next(chip)
