import random
import math

from underworld import function as fn
from planetengine.utilities import get_prioritySubstrate
from everest.built import Built

def build(*args, **kwargs):
    built = BasicNoise(*args, **kwargs)
    return built

class BasicNoise(Built):

    def __init__(
            self,
            dims = 2,
            pert = 1e-6,
            freq = 1e6,
            iterations = 6,
            seed = 1066,
            ):

        inputs = locals().copy()

        randTerms = []
        coordFns = fn.coord()
        normFn = lambda x: 1. / math.sqrt(2.) * (x + 1.)
        dimFns = []
        for dim in range(dims):
            dimFreq = freq
            dimPert = pert ** (1. / dims)
            dimFn = fn.misc.constant(1.)
            for i in range(iterations):
                randPhase = fn.misc.constant(1.)
                randFreq = fn.misc.constant(1.)
                randPert = fn.misc.constant(1.)
                freqTerm = dimFreq * normFn(randFreq)
                phaseTerm = randPhase * math.pi
                pertTerm = dimPert * normFn(randPert)
                sinFn = pertTerm * fn.math.sin(freqTerm * (coordFns[dim] + phaseTerm))
                localRands = {
                    'phase': randPhase,
                    'freq': randFreq,
                    'pert': randPert
                    }
                randTerms.extend([randPhase, randFreq, randPert])
                dimFreq *= math.sqrt(2.)
                dimPert /= math.sqrt(2.)
                dimFn += sinFn
            dimFns.append(dimFn)
        waveFn = fn.misc.constant(1.)
        for dimFn in dimFns:
            waveFn *= dimFn

        self.seed = seed
        self.waveFn = waveFn
        self.randTerms = randTerms
        self._preditherings = dict()
        self._ditherings = dict()
        self._system = None

        super().__init__(
            inputs = inputs,
            script = __file__
            )

    def randomise(self, seed = 0):
        random.seed((self.seed, seed))
        for randTerm in self.randTerms:
            randTerm.value = random.random()
        random.seed()

    def __enter__(self):
        system = self._system
        for index, (varName, var) \
                in enumerate(sorted(system.varsOfState.items())):
            self._preditherings[varName] = var.data.copy()
            self.randomise((system.count(), index))
            substrate = get_prioritySubstrate(var)
            dithering = self.waveFn.evaluate(substrate)
            var.data[:] *= dithering
        system.clipVals()
        system.setBounds()

    def __exit__(self, *args):
        system = self._system
        exc_type, exc_value, tb = args
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        for varName, var in sorted(system.varsOfState.items()):
            var.data[:] = self._preditherings[varName]
        return True
