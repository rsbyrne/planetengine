import numpy as np
from planetengine.initials._IC import _IC

def build(*args, name = None, **kwargs):
    built = IC(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class IC(_IC):

    varDim = 1
    meshDim = 2
    script = __file__

    def __init__(
            self,
            *args,
            pert = 0.2,
            freq = 1.,
            phase = 0.,
            **kwargs
            ):

        inputs = locals().copy()

        self.valRange = (0., 1.)

        self.freq = freq
        self.phase = phase
        self.pert = pert

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script
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
