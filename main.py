from enum import unique
from typing import List, Optional
from enum import Enum, auto
import wave
import struct

@unique
class WaveData(Enum):
    """
    Raw wave data with 32 values between 0 and 15 (4 bits).
    """
    square_50 = 16 * [0] + 16 * [15]
    triangle = [ i for i in range(16)] + [ i for i in range(15,-1,-1)]
    saw_up = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15]
    noise = 2 * [0,15,15,0, 15,0,0,15, 15,15,0,0, 15,15,0,15]

@unique
class EnvelopeData(Enum):
    """
    Envelopes to shape the output of an oscillator. 
    """
    ramp_up = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15]

class Waveform():
    """
    A waveform iterator of length 32
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

@unique
class Envelope(Enum):
    """
    16 step envelopes with values between 0.0 and 1.0 for attenuating oscillator output.
    """
    ramp_up = [ v/15 for v in range(0,16) ]
    ramp_down = list(reversed([ v/15 for v in range(0,16) ]))
    on = 16 * [1.0]
    off = 16 * [0.0]

class Attenuator():
    """
    Time based attenuation with 16 (4 bits) steps of values between 0-15 (4 bits)
    """

    def __init__(self, envelope=Envelope.on, sample_rate = 44100, freq = 64):
        
        self._sample_rate = sample_rate
        self._freq = freq
        self._envelope = envelope.value
        assert len(self._envelope) == 16

        self._samples_pr_step: float = self._sample_rate / self._freq

        self._samples_served = 0

        print("Samples pr step: ",self._samples_pr_step)
        print("Enevlope: ", self._envelope )

        self.reset()

    @property
    def sample_rate(self):
        return self._sample_rate

    def reset(self):
        self._pos = 0
        self._samples_served = 0

    def __iter__(self):
        return self

    def __next__(self):
        # Get the value for the current step of envelope.
        # Value is 0 if envelope is over 
        try:
            v = self._envelope[self._pos]
        except IndexError:
            return self._envelope[-1]

        self._samples_served += 1

        # Advance to next position in the envelope
        if self._samples_served >= self._samples_pr_step:
            self._pos += 1
            self._samples_served -= self._samples_pr_step
        #print(self._samples_served)
        #print(self._pos)
        return v


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
        self._attenuators: List[Attenuator] = []
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

    def add_oscillator(self, o: Oscillator, envelope: Optional[Envelope] = Envelope.on) -> int:
        """
        Add an oscillator. Return the index of the new oscillator.
        """
        # Oscillator must match mixer's sample rate
        assert o.sample_rate == self._sample_rate
        self._oscillators.append(o)

        # Add an attenuator for the oscillator
        self._attenuators.append(Attenuator(sample_rate=self._sample_rate, envelope=envelope))
        return len(self._oscillators) - 1

    def __iter__(self):
        return self

    def __next__(self) -> int:
        """
        Sum of all oscillators divided by no of oscillators.
        """
        # Build a list of oscillators outputs attenuated by amplifiers
        v = []
        for i in range(len(self._oscillators)):
            a = next(self._attenuators[i])
            o = next(self._oscillators[i])
            # print("a:", a, "o", o)
            v.append(self._volume * a * o)

        # Sum the outputs and divide by nr. of oscillators
        return int(sum(v) / len(self._oscillators))

#o_sq50_1 = Oscillator(wave_data = WaveData.square_50, freq=220)
#o_sq50_2 = Oscillator(wave_data = WaveData.square_50, freq=210)

o_saw = Oscillator(wave_data = WaveData.saw_up, freq=220)
o_tri = Oscillator(wave_data = WaveData.triangle, freq=220)
#o_noise = Oscillator(wave_data = WaveData.noise, freq=110)


m = Mixer()
#m.add_oscillator(o_sq50_1)
#m.add_oscillator(o_sq50_2)

m.add_oscillator(o_saw, Envelope.ramp_down)
m.add_oscillator(o_tri, Envelope.ramp_up)

wave_file = wave.open('test.wav', "wb")
wave_file.setnchannels(1) # Mono
wave_file.setframerate(m.sample_rate)
wave_file.setsampwidth(2)

# Get samples from mixer. Write to file.
for i in range(3 * m.sample_rate):
    #print([ next(o) for i in range(64)])
    v = 100 * (next(m))
    #print(v)
    s = struct.pack('<h', v)
    wave_file.writeframesraw(s)

wave_file.close()