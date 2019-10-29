import random
import numpy as np

import underworld as uw
_fn = uw.function
UWFn = _fn._function.Function

from . import _basetypes
from . import _planetvar
from .. import utilities
hasher = utilities.hashToInt

class Parameter(_basetypes.BaseTypes):

    opTag = 'Parameter'

    def __init__(self, inFn, **kwargs):

        initialVal = inFn()
        var = _fn.misc.constant(initialVal)
        if not len(list(var._underlyingDataItems)) == 0:
            raise Exception

        self._hashVars = []
        self.stringVariants = {}
        self.inVars = []
        self.parameters = []
        self.var = var
        self.mesh = self.substrate = None

        self._paramfunc = inFn
        self._hashval = random.randint(1, 1e18)

        self._update_attributes()
        sample_data = np.array([[val,] for val in self.value])
        self.dType = _planetvar.get_dType(sample_data)

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return random.randint(0, 1e18)

    def _update_attributes(self):
        self.value = self.var.evaluate()[0]
        # self.data = np.array([[val,] for val in self.value])

    def _partial_update(self):
        self.var.value = self._paramfunc()
        self._update_attributes()

    def __hash__(self):
        return self._hashval
