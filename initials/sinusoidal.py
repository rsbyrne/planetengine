import numpy as np

def build(*args, **kwargs):
    return IC(*args, **kwargs)

class IC:

    def __init__(
            self,
            pert = 0.2,
            freq = 1.,
            phase = 0.
            ):

        self.inputs = locals().copy()
        del self.inputs['self']
        self.scripts = [__file__,]

        self.valRange = (0., 1.)

        self.freq = freq
        self.phase = phase
        self.pert = pert

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
