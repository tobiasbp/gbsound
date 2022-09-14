from enum import unique
from random import sample
from typing import List, Optional
from enum import Enum, auto
import wave
import struct

@unique
class Note(Enum):
    A = 220
    B = 246.94
    C = 261.63
    D = 293.66
    E = 329.63
    F = 349.23
    G = 392.00

@unique
class WaveData(Enum):
    """
    Raw wave data with 32 values between 0 and 15 (4 bits).
    """
    square_50 = 16 * [0] + 16 * [15]
    triangle = [ i for i in range(16)] + [ i for i in range(15,-1,-1)]
    saw_up = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15]
    noise = 2 * [0,15,15,0, 15,0,0,15, 15,15,0,0, 15,15,0,15]

class Timer():
    """
    A timer returning True at the specified frequency
    """

    def __init__(self, sample_rate=44100, freq=256):
        self._value = None
        self._running = True

        # The number of ticks before timer rolls backs
        self._length: float = sample_rate / freq

        self.reset()
        
    def reset(self):
        self._value = 0
        self._running = True

    def stop(self):
        self._running = False

    #def __iter__(self):
    #    return self
    
    #def __next__(self):
    def tick(self):
        if not self._running:
            v = False
        elif self._value > self._length:
            self._value -= self._length
            v = True
        else:
            v = False
        
        self._value += 1

        return v

class Waveform():

    def __init__(self, data, sample_rate:int = 44100, freq:int = 440):
        self._data = data
        self._sample_rate = sample_rate
        self._freq = freq

        self._timer = None
        self._data_pos = None

        self.reset()
    
    def reset(self):
        self._timer = Timer(sample_rate=self._sample_rate, freq=len(self._data) * self._freq)
        self._data_pos = 0
    
    def set_freq(self, freq: int):
        self._freq = freq
        self.reset()
    
    def set_waveform(self, data: List[int]):
        assert len(data) == len(self._data), "Length of new waveform does not match existing waveform"
        self._data = data

    def __iter__(self):
        return self

    def __next__(self):
        v = self._value = self._data[self._data_pos]
        
        if self._timer.tick():
            self._data_pos += 1
            # Loop back
            if self._data_pos == len(self._data):
                self._data_pos = 0

        return v

class Channel():

    def __init__(self, data=[], sample_rate:int=44100, freq:int=440, volume:int=15 , enabled:bool=True):
        self._current_volume = volume
        self._base_volume = volume
        self._sample_rate = sample_rate
        self._enabled = enabled
        self._freq = freq

        self._envelope_add = False
        self._envelope_timer = Timer(sample_rate=sample_rate, freq=64)

        self._sweep_timer = Timer(sample_rate=sample_rate, freq=128)

        # If enabled, the counter will disable the channel when the counter reaches 0
        self._length_value = 64
        self._length_enabled = False
        self._lengt_counter = self._length_value
        self._length_timer = Timer(sample_rate=sample_rate, freq=256)

        # The waveform to play (oscillator)
        self._waveform = Waveform(
            data=data if any(data) else self._build_square_wave(duty_cycle=0.5, length=32),
            #data=WaveData.triangle.value,
            sample_rate=sample_rate,
            freq=freq
            )

    @property
    def sample_rate(self):
        return self._sample_rate
    
    @property
    def waveform(self):
        return self._waveform

    @property
    def freq(self):
        return self._waveform.freq

    @freq.setter
    def freq(self, freq):
        self._waveform.set_freq(freq)

    def trig(self) -> None:
        # Enable the channel
        self._enabled = True
        
        # Reset length timer if it has reached end
        if self._lengt_counter == 0:
            self._length_timer.reset()
            self._lengt_counter = self._length_value

        # Wave channel's position is set to 0 but sample buffer is NOT refilled.
        self._waveform.reset()

        # Reset envelope timer
        self._envelope_timer.reset()

        # Channel volume is reloaded from NRx2.
        self._current_volume = self._base_volume

        # Noise channel's LFSR bits are all set to 1.
        # Square 1's sweep does several things (see frequency sweep).

    def _build_square_wave(self, duty_cycle: float, length=32) -> List[int]:
        """
        Build a square wave from a duty cycle
        """
        # One or more ON entries in waveform
        no_of_on_entries = max(1, int(duty_cycle * length))
        # The rest of the entries are off
        no_of_off_entries = length - no_of_on_entries
        # Build the wavedata
        d = no_of_off_entries * [0] + no_of_on_entries * [15]
        assert len(d) == length, f"Waveform must have {length} values"
        return d

    def set_waveform(self, data: List[int]):
        """
        Set the waveform to a waveform matching length of existing waveform. 
        """
        self._waveform.set_waveform(data)
    
    def set_duty_cycle(self, duty_cycle):
        """
        Replace existing waveform with a square with a duty cycle of duty_cycle
        """
        self._waveform.set_waveform(
            self._build_square_wave(duty_cycle, len(self._waveform._data))
        )

    def set_length(self, length):
        self._length_value = length

    def __iter__(self):
        return self

    def __next__(self) -> float:
        
        if self._length_enabled and self._length_timer.tick():
            self._lengt_counter -= 1
            if self._lengt_counter == 0:
                self._enabled = False
                self._length_timer.stop()

        # If the envelope timer overflowed
        if self._envelope_timer.tick():
            # Calculate new volume
            nv = self._current_volume + (1 if self._envelope_add else -1)
            # If new volume is valid, use it. If not, stop timer
            if 0 <= nv <= 15:
                self._current_volume = nv
            else:
                self._envelope_timer.stop()

        w = next(self._waveform)

        if self._enabled:
            return self._current_volume * w
        
        return 0.0

class Chip():
    """
    A programmable sound generator
    """
    def __init__(self, sample_rate=44100):
        self._channels = [
            Channel(sample_rate=sample_rate, freq=440),
            Channel(sample_rate=sample_rate, freq=220),
            Channel(sample_rate=sample_rate, freq=110),
        ]
        # Set waveforms for channels
        self._channels[0].set_duty_cycle(0.5)
        self._channels[1].set_duty_cycle(0.5)
        self._channels[2].set_waveform(WaveData.triangle.value)

        self._sample_rate = sample_rate
        

    @property
    def sample_rate(self):
        return self._sample_rate
    
    def trig(self, channel: Optional[int] = None):
        """
        Trig one or all channels
        """
        if channel:
            self._channels[channel].trig()
        else:
            for c in self._channels:
                c.trig()

    def set_freg(self, freq: int, channel: Optional[int] = None):
        """
        Set one frequency for one or all channels
        """
        if channel:
            self._channels[channel].freq = freq
        else:
            for c in self._channels:
                c.freq = freq

    def set_fregs(self, freqs: List[int]):
        """
        Set the frequency for all channels
        """
        assert len(self._channnels) == len(freq)
        for i in (range(len(freqs))):
                self._channels[i].freq  = freqs[i]

    def __iter__(self):
        return self

    def __next__(self):
        return sum([ next(c) for c in self._channels]) / len(self._channels)


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
