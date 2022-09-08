    

class SquareChannel():
    # Enevlopes are linear
    samples_pr_cycle = 32

    def __init__(self, freq:int=440, duty_cycle: int = 2):
        assert duty_cycle in [0,1,2,3]

        self.samples_pr_cycle:int=32
        assert self.samples_pr_cycle % 2 == 0
        
        self.duty_cycle = duty_cycle
        # The waveform
        self.freq = freq

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

    def sample(self, delta_time):
        self._time_ms += delta_time
        step_no = (self._time_ms % self._wave_length_ms) // self.__step_size_ms
        return self.wave[int(step_no)]
    

w = SquareChannel(freq=1)

print( [ w.sample(1000/32) for i in range(32*1)])

print("Time passed:", w.time_ms)
print(w.freq)
print((440 * 32 * w.step_size_ms))
