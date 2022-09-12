from enum import unique
from typing import List
from enum import Enum, auto
import wave
import struct

@unique
class WaveData(Enum):
    """
    Wave data with values between 0 and 15 (4 bits).
    """
    square_50 = 16 * [0] + 16 * [15]
    triangle = [ i for i in range(16)] + [ i for i in range(15,-1,-1)]
    saw_up = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15]
    noise = 2 * [0,15,15,0, 15,0,0,15, 15,15,0,0, 15,15,0,15]

class Waveform():
    """
    A waveform of length 32
    """

    def __init__(self, wave_data: WaveData):
        self._wave: List[int] = wave_data.value
        self._pos: int = 0
        self._length = len(self._wave)

        assert self._length == 32

    def __iter__(self):
        return self

    def __next__(self) -> int:
        """
        Return the next value in the waveform
        """
        v =  self._wave[self._pos]
        
        if self._pos == len(self._wave) - 1:
            self._pos = 0
        else:
            self._pos += 1
        
        return v

    def __len__(self):
        return self._length


class SquareChannel():
    # Envelopes are linear
    samples_pr_cycle = 32

    def __init__(self, freq:int=440, duty_cycle: int = 2, sample_rate=44100, buffer_size=256):
        assert duty_cycle in [0,1,2,3]

        self.samples_pr_cycle:int=32
        assert self.samples_pr_cycle % 2 == 0
        
        self.duty_cycle = duty_cycle
        # The waveform
        self.freq = freq
        self.sample_rate = sample_rate

    @property
    def duty_cycle(self):
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, new_duty_cycle):
        on_samples =  [4, 8, 16, 24][new_duty_cycle]
        off_samples = SquareChannel.samples_pr_cycle - on_samples
        self.wave = off_samples * [0] + on_samples * [15]
        self._duty_cycle = new_duty_cycle

    @property
    def freq(self):
        return self._freq
    
    @freq.setter
    def freq(self, new_freq):
        self.__step_size_ms: float = 1000 / (new_freq * SquareChannel.samples_pr_cycle)
        self._freq = new_freq
        self._time_ms = 0.0
        self._wave_length_ms = SquareChannel.samples_pr_cycle * self.__step_size_ms

    @property
    def step_size_ms(self):
        return self.__step_size_ms

    @property
    def time_ms(self):
        return self._time_ms

    def get_samples():
        """
        Get the next no_of_sample samples
        """
    #def sample(self, delta_time):
    #    self._time_ms += delta_time
    #    step_no = (self._time_ms % self._wave_length_ms) // self.__step_size_ms
    #    return self.wave[int(step_no)]
    
class Oscillator():

    def __init__(self, wave_data: WaveData = WaveData.square_50, sample_rate=44100, freq=1):
        self._waveform = Waveform(wave_data)
        self._sample_rate = sample_rate
        # The number of values to get from the wave data pr. sample
        self._samples_pr_wave_value = sample_rate / (freq * len(self._waveform)) 
        print("samples_pr_wave_value:", self._samples_pr_wave_value)

        assert self._samples_pr_wave_value >= 1.0, f"Sample rate too low. Ratio is: {self._samples_pr_wave_value}"
        
        # Current output from oscillator is first value in waveform
        self._value = next(self._waveform)
        # Since ratio is not always an int, we need to considet parts of samples
        self._samples_served: float = 0.0

    @property
    def sample_rate(self):
        return self._sample_rate

    def __iter__(self):
        return self

    def __next__(self):
        # The value to return
        v = self._value

        self._samples_served += 1.0
        if self._samples_served >= self._samples_pr_wave_value:
            # oscillator now has this output
            self._value = next(self._waveform)
            # Reset count towards next time we update the output
            self._samples_served -= self._samples_pr_wave_value

        # Shift down by 8 becauze we have 16 values in waveforms
        return v - 7


class Mixer():
    """
    An iterator mixing a number of oscillators.
    """
    def __init__(self, sample_rate = 44100):
        self._oscillators: List[Oscillator] = []
        self._sample_rate = sample_rate
        self._volume = 10

    @property
    def no_of_oscillators(self):
        """
        How many oscillators in the mixer.
        """
        return len(self._oscillators)

    @property
    def sample_rate(self):
        return self._sample_rate

    def add_oscillator(self, o: Oscillator) -> int:
        """
        Add an oscillator. Return the index of the new oscillator.
        """
        # Oscillator must match mixer's sample rate
        assert o.sample_rate == self._sample_rate
        self._oscillators.append(o)
        return len(self._oscillators)-1

    def __iter__(self):
        return self

    def __next__(self) -> int:
        """
        Sum of all oscillators divided by no of oscillators.
        """
        # FIXME: 4 bits here?
        v = sum( [ next(o) for o in self._oscillators ] ) // len(self._oscillators)
        return int(self._volume * v)

o_sq50_1 = Oscillator(wave_data = WaveData.square_50, freq=220)
o_sq50_2 = Oscillator(wave_data = WaveData.square_50, freq=210)

o_saw = Oscillator(wave_data = WaveData.saw_up, freq=220)
o_tri = Oscillator(wave_data = WaveData.triangle, freq=110)
o_noise = Oscillator(wave_data = WaveData.noise, freq=110)


m = Mixer()
#m.add_oscillator(o_sq50_1)
#m.add_oscillator(o_sq50_2)

#m.add_oscillator(o_noise)
m.add_oscillator(o_tri)

wave_file = wave.open('test.wav', "wb")
wave_file.setnchannels(1) # Mono
wave_file.setframerate(m.sample_rate)
wave_file.setsampwidth(2)

# Get samples from mixer. Write to file.
for i in range(2 * m.sample_rate):
    #print([ next(o) for i in range(64)])
    v = 100 * (next(m))
    s = struct.pack('<h', v)
    wave_file.writeframesraw(s)

wave_file.close()