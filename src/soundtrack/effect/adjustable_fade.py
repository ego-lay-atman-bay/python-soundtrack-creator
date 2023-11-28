import numpy

from .effect import Effect

class AdjustableFade(Effect):
    OPTIONS = {
        'gain0': {
            'default': 1,
            'type': float,
        },
        'gain1': {
            'default': 0,
            'type': float,
        },
        'curve_ratio': {
            'default': 0,
            'type': float,
        }
    }
    
    def get(self) -> numpy.ndarray:
        return self.linear_fade(
            gain0 = self.options['gain0'],
            gain1 = self.options['gain1'],
            curve_ratio = self.options['curve_ratio'],
            length = self.length,
        )
    
    def gainscale(gain):
        return gain / 100.0

    def linear_fade(
        self,
        gain0: float,
        gain1: float,
        curve_ratio: float,
        length: int,
    ) -> numpy.ndarray[float]:
        """Generate fade scaler for the specified length.

        Args:
            gain0 (float): Start gain
            gain1 (float): End gain
            curve_ratio (float): Mid-fade adjust (%) between 0 and 1
            length (int): Sample length of the fade (not sample rate).

        Returns:
            numpy.ndarray[float]: numpy array
        """
        if (gain0 == gain1):
            return numpy.array([gain0] * length)
        elif ((curve_ratio > 0) and (curve_ratio < 0.5)):
            _curve_ratio = curve_ratio * 2
            return ((self.scale_curve(gain0, gain1, self.linear(gain0, gain1, length)) * (1 - _curve_ratio)) +
                    (self.scale_curve(gain0, gain1, self.cosine_curve(gain0, gain1, length)) * _curve_ratio))
        elif (curve_ratio > 0):
            return self.cos_curve(gain0, gain1, 1.5 - curve_ratio, length)
        else:
            return self.simple_curve(gain0, gain1, (1 - (2 * curve_ratio)), length)

    def simple_curve(
        self,
        gain0: float,
        gain1: float,
        power: float,
        length: int,
    ) -> numpy.ndarray[float]:
        return self.curve_adjust(gain0, gain1, power, self.linear(gain0, gain1, length))
        
    def scale_curve(
        self,
        gain0: float,
        gain1: float,
        env: numpy.ndarray[float],
    ) -> numpy.ndarray[float]:
        return min(gain0, gain1) + (abs(gain0 - gain1) * env)

    def linear(
        self,
        gain0: float,
        gain1: float,
        length: int,
    ) -> numpy.ndarray[float]:
        return numpy.linspace(gain0, gain1, length)
            

    def cosine_curve(
        self,
        gain0: float,
        gain1: float,
        length: int,
    ) -> numpy.ndarray[float]:
        """Creates half a cosine wave of the specified length

        Args:
            gain0 (float): gain0
            gain1 (float): gain1
            length (int): length

        Returns:
            numpy.ndarray: numpy array
        """
        phase = 1 if (gain0 > gain1) else -1
        return (numpy.cos(numpy.deg2rad((numpy.arange(length) / length) * 180)) * phase + 1) * 0.5

    def cos_curve(
        self,
        gain0: float,
        gain1: float,
        power: float,
        length: int,
    ) -> numpy.ndarray[float]:
        return self.curve_adjust(gain0, gain1, power, self.cosine_curve(gain0, gain1, length))

    def curve_adjust(
        self,
        gain0: float,
        gain1: float,
        power: float,
        env: numpy.ndarray[float],
    ) -> numpy.ndarray[float]:
        return self.scale_curve(gain0, gain1,
            (env if (power == 1) else numpy.exp(power * numpy.log(env))))

