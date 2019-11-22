import numpy as np
from planetengine._IC import IC

def build(*args, name = None, **kwargs):
    built = Sinusoidal(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Sinusoidal(IC):

    def __init__(
            self,
            pert = 0.2,
            freq = 1.,
            phase = 0.,
            ):

        inputs = locals().copy()

        self.valRange = (0., 1.)

        self.freq = freq
        self.phase = phase
        self.pert = pert

        super().__init__(
            inputs = inputs,
            script = __file__,
            evaluate = self.evaluate
            )

    def evaluate(self, coordArray):
        valMin, valMax = self.valRange
        deltaVal = self.valRange[1] - self.valRange[0]
        pertArray = \
            self.pert \
            * np.cos(np.pi * (self.phase + self.freq * coordArray[:,0])) \
            * np.sin(np.pi * coordArray[:,1])
        outArray = valMin + deltaVal * (coordArray[:,1]) + pertArray
        outArray = np.clip(outArray, valMin, valMax)
        outArray = np.array([[item] for item in outArray])
        return outArray
