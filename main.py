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
    16 step envelopes with values between 0.0 and 1.0 for attenuating oscillator output.
    """
    ramp_up = [ v/15 for v in range(0,16) ]
    ramp_down = list(reversed([ v/15 for v in range(0,16) ]))
    on = 16 * [1.0]
    off = 16 * [0.0]

class ClockedData():
    """
    Looping clocked data
    """

    def __init__(self, data, sample_rate:int = 44100, freq:int = 64):

        self._data = data
        self._sample_rate = sample_rate
        self._freq = freq

        self._update_samples_pr_step()
        self.reset()

    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, v):
        print("Freq set:", v)
        self._freq = v
        self._update_samples_pr_step()
        
    @property
    def sample_rate(self):
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, sr):
        self._sample_rate = sr
        self._update_samples_pr_step()

    def reset(self):
        self._pos = 0
        self._samples_served = 0

    def _update_samples_pr_step(self):
        self._samples_pr_step: float = self._sample_rate / self._freq
    
    def _tick(self):
        """
        Advance time each time a sample has been served.
        Return True of this tick caused us to advance to the next step.
        """
        self._samples_served += 1
        # Advance to next position in the data
        if self._samples_served >= self._samples_pr_step:
            self._samples_served -= self._samples_pr_step
            return True

        return False

    def __iter__(self):
        return self

    def __next__(self):
        # Get the value for the current step of envelope.
        v = self._data[self._pos]

        if self._tick():
            self._pos += 1

        # Loop        
        if self._pos == len(self._data):
            self._pos = 0

        return v

class Envelope(ClockedData):
    """
    Run through the envelope data.
    Once the last value has been reached, return that value forever.
    """

    def __next__(self):
        # FIXME: I think this will return 0 on the first call. It should return envelope data.
        try:
            v = self._data[self._pos]
        except IndexError:
            pass
        else:
            if self._tick():
                self._pos += 1
                return v

        return 0

class Waveform(ClockedData):
    """
    A waveform for generating sound (oscillator).
    """
    def _update_samples_pr_step(self):
        self._samples_pr_step: float = self._sample_rate / (len(self._data) * self._freq)
        print("Update sample:", self._freq)

class Length(ClockedData):
    """
    A timer for setting enabling and disabling a channel.
    """

    @property
    def status(self) -> bool:
        try:
            self._data[self._pos]
        except IndexError:
            return False
        else:
            return True

    def __next__(self) -> bool:
        # False if we reached the end of the data, True otherwise.
        v = self.status

        if self._tick():
            self._pos += 1

        return v

class Channel():

    def __init__(self, sample_rate:int=44100, freq:int=440, volume:int=15 , enabled:bool=True):
        self._current_volume = volume
        self._base_volume = volume
        self._sample_rate = sample_rate
        self._enabled = enabled

        # The envelope attenuating the output
        self._envelope = Envelope(
            data = [],
            sample_rate=sample_rate,
            freq=64
            )

        # The waveform to play (oscillator)
        self._waveform = Waveform(
            data=WaveData.triangle.value,
            sample_rate=sample_rate,
            freq=freq
            )

        self._length = Length(
            sample_rate=sample_rate,
            data = [ n for n in range(256//4) ],
            freq = 256
        )
    @property
    def sample_rate(self):
        return self._sample_rate

    @property
    def freq(self):
        return self._waveform.freq

    @freq.setter
    def freq(self, v):
        print("New freq", v)
        self._waveform.freq = v

    def trig(self) -> None:
        # Enable the channel
        self._enabled = True
        
        # Reset length timer if it has reached end
        if not self._length.status:
            self._length.reset()

        # Wave channel's position is set to 0 but sample buffer is NOT refilled.
        self._waveform.reset()

        self._envelope.reset()

        # Channel volume is reloaded from NRx2.
        self._current_volume = self._base_volume

        # Noise channel's LFSR bits are all set to 1.
        # Square 1's sweep does several things (see frequency sweep).

    def set_waveform(wf: WaveData):
        pass

    def __iter__(self):
        return self
    
    def __next__(self) -> float:
        self._enabled = next(self._length)

        # Modify volume by envelope
        self._current_volume += next(self._envelope)
        # Clamp value to range 0-15
        self._current_volume = min(15, max(0, self._current_volume))

        #self.volume = next(self._envelope)
        
        w = next(self._waveform)

        if self._enabled:
            return self._current_volume * w
            #return (self.volume * e * w) / 2
        
        return 0.0

class Attenuator():
    """
    Time based attenuation with 16 (4 bits) steps of values between 0-15 (4 bits)
    """

    def __init__(self, envelope=EnvelopeData.on, sample_rate = 44100, freq = 64):
        
        self._sample_rate = sample_rate
        self._freq = freq

        self._envelope = envelope.value
        assert len(self._envelope) == 16

        self._samples_pr_step: float = self._sample_rate / (self._freq)

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

class SquareChannel(Channel):
    """
    A channel with square waves
    """

    def __init__(self, sample_rate:int=44100, freq:int=440, volume:int=15 , enabled:bool=True, duty_cycle: float = 0.5):

        super().__init__(sample_rate=sample_rate, freq=freq, volume=volume , enabled=enabled)

        # Reconfigure the waveform
        self.set_duty_cycle(duty_cycle)

    @property
    def duty_cycle(self) -> float:
        """
        Return the current duty cycle
        """
        return self._duty_cycle

    def set_duty_cycle(self, ds):
        """
        Replace waveform with a square with a duty cycle of ds
        """
        self._duty_cycle = ds
        self._waveform=Waveform(
            data=self._build_square_wave(ds) ,
            sample_rate=self._sample_rate,
            freq=self.freq
            )

    def _build_square_wave(self, ds: float) -> List[int]:
        """
        Build a square wave from a duty cycle
        """
        # One or more ON entries in waveform
        no_of_on_entries = max(1, int(self._duty_cycle * 32))
        # The rest of the entries are off
        no_of_off_entries = 32 - no_of_on_entries
        # Build the wavedata
        return no_of_off_entries * [0] + no_of_on_entries * [15]


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

    def add_oscillator(self, o: Oscillator, envelope: Optional[EnvelopeData] = EnvelopeData.on) -> int:
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

class Chip():
    """
    A programmable sound generator
    """
    def __init__(self, sample_rate=44100):
        self._channels = [
            SquareChannel(sample_rate=sample_rate, freq=440),
            Channel(sample_rate=sample_rate, freq=220),
            Channel(sample_rate=sample_rate, freq=110),
        ]
    
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
        Set the frequency for one or all channels
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
    



m = Mixer()

#m.add_oscillator(o_saw, EnvelopeData.ramp_down)
#m.add_oscillator(o_tri, EnvelopeData.ramp_up)

#m = Channel()

chip = Chip()
wave_file = wave.open('test.wav', "wb")
wave_file.setnchannels(1) # Mono
wave_file.setframerate(m.sample_rate)
wave_file.setsampwidth(2) # Bytes to use for samples

for f in [110, 220, 440, 880]:
    for i in range(m.sample_rate//2):
        v = 100 * (next(chip))
        s = struct.pack('<h', int(v))
        wave_file.writeframesraw(s)
    chip.set_freg(f,0)
    chip.trig(0)

# Get samples from mixer. Write to file.
"""
for f in [110, 220, 440, 880]:
    m.freq = f
    m.trig()
    for i in range(1 * m.sample_rate):
        v = 100 * (next(m))
        s = struct.pack('<h', int(v))
        wave_file.writeframesraw(s)
"""

wave_file.close()
