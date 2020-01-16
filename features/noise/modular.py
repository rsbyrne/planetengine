import numpy as np

from . import Noise

def build(*args, **kwargs):
    built = Modular(*args, **kwargs)
    return built

class Modular(Noise):

    def __init__(
            self,
            intensity = 6,
            seed = 1066,
            ):

        inputs = locals().copy()
        self.seed = seed
        self.intensity = intensity
        super().__init__(
            inputs,
            script = __file__
            )

    def apply(self, var, seed):
        inArr = var.data
        ditherFactor = 10 ** (8 - self.intensity)
        modArr = inArr * ditherFactor
        modArrInt = np.where(modArr <= 1., 1, modArr.astype('int'))
        clippedArr = inArr - modArr % modArrInt / ditherFactor
        np.random.seed((self.seed, *seed))
        inArr[...] = clippedArr + np.random.random(clippedArr.shape) / ditherFactor
        np.random.seed()
