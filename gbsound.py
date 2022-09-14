from enum import unique
from typing import List, Optional
from enum import Enum
from random import randint

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
    triangle = [ i for i in range(16)] + list(reversed([ i for i in range(16)]))
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
    
    @property
    def freq(self):
        return self._freq

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

class Noise():

    def __init__(self):
        self.enabled = False
        self.volume = 15

    def trig(self):
        pass

    def sweep_up(self, sweep_up):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if not self.enabled:
            return 0

        return self.volume * randint(0,16)

class Channel():

    def __init__(self, data=[], sample_rate:int=44100):
        # The volume to return to when triggered
        self._base_volume = 15
        # The volume in use
        self._current_volume = self._base_volume
        self._sample_rate = sample_rate
        self._freq = 440

        # Not playing
        self._enabled = False

        self._envelope_add = False
        self._envelope_timer = Timer(sample_rate=sample_rate, freq=64)

        # Timer based manipulation of waveform frequency
        self._sweep_up = True
        self._sweep_enabled = False
        self._sweep_timer = Timer(sample_rate=sample_rate, freq=32)

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
            freq=self._freq
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

        self._sweep_timer.reset()

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

    def sweep_enable(self, enable: bool):
        self._sweep_enabled = enable

    def sweep_up(self, sweep_up: bool):
        self._sweep_up = sweep_up

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

        # Sweep timer
        if self._sweep_enabled and self._sweep_timer.tick():

            # Original frequency
            f_o = self._waveform._freq

            # Double or half frequency depending of direction of sweep
            if self._sweep_up:
                f_n = f_o * 2
            else:
                f_n = max(1, f_o * 0.5)

            self._waveform.set_freq(f_n)

        # Length timer
        if self._length_enabled and self._length_timer.tick():
            self._lengt_counter -= 1
            if self._lengt_counter == 0:
                self._enabled = False
                self._length_timer.stop()

        # Envelope timer
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
            # Values between -1.0 and 1.0 multiplied by volume
            return self._current_volume * (((w/15) * 2) - 1)
        
        return 0.0

class Chip():
    """
    A programmable sound generator
    """
    def __init__(self, sample_rate=44100):
        self._channels = [
            Channel(sample_rate=sample_rate), # Square
            Channel(sample_rate=sample_rate), # Square
            Channel(sample_rate=sample_rate), # Wave
            Noise(), # Noise

        ]
        # Set waveforms for channels
        self._channels[0].set_duty_cycle(0.5)
        self._channels[1].set_duty_cycle(0.5)
        self._channels[2].set_waveform(WaveData.triangle.value)

        self._sample_rate = sample_rate

        self.volume = 400
        

    @property
    def sample_rate(self):
        return self._sample_rate
    
    def trig(self, channel: Optional[int] = None):
        """
        Trig one or all channels
        """
        if channel is None:
            for c in self._channels:
                c.trig()
        else:
            self._channels[channel].trig()

    def sweep_enable(self, enable: bool, channel: Optional[int] = None):
        """
        Enable/disable sweep for one or all channels
        """
        if channel is None:
            for c in self._channels:
                c.sweep_enable(enable)
        else:
            self._channels[channel].sweep_enable(enable)

    def sweep_up(self, sweep_up: bool, channel: Optional[int] = None):
        """
        Set sweep direction for one or all channels
        """
        if channel is None:
            for c in self._channels:
                c.sweep_up(sweep_up)
        else:
            self._channels[channel].sweep_up(sweep_up)

    def set_freg(self, freq: int, channel: Optional[int] = None):
        """
        Set one frequency for one or all channels
        """
        if channel is None:
            for c in self._channels:
                c.freq = freq
        else:
            self._channels[channel].freq = freq

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
        #v = [v for v in [ next(c) for c in self._channels] if v != 0] 
        
        #try:
        #    return self.volume * (sum(v) / len(v))
        #except ZeroDivisionError:
        #    return 0
        #for n, c in enumerate(self._channels):
        #    print(f"Channel {n}: {next(c)}")
        #c_0 = next(self._channels[0])
        #c_1 = next(self._channels[1])
        #c_2 = next(self._channels[2])
        
        

        #return self.volume * next(self._channels[0])
        return self.volume * sum([ next(c) for c in self._channels]) / len(self._channels)
