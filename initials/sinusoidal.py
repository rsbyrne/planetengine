import numpy as np
from planetengine.initials import IC

class Sinusoidal(IC):

    script = __file__

    def __init__(
            self,
            pert = 0.2,
            freq = 1.,
            phase = 0.,
            **kwargs
            ):

        valRange = (0., 1.)
        freq = freq
        phase = phase
        pert = pert

        def evaluate(coordArray):
            valMin, valMax = valRange
            deltaVal = valRange[1] - valRange[0]
            pertArray = \
                pert \
                * np.cos(np.pi * (phase + freq * coordArray[:,0])) \
                * np.sin(np.pi * coordArray[:,1])
            outArray = valMin + deltaVal * (1. - coordArray[:,1]) + pertArray
            outArray = np.clip(outArray, valMin, valMax)
            outArray = np.array([[item] for item in outArray])
            return outArray

        super().__init__(evaluate, **kwargs)

CLASS = Sinusoidal
