import numpy as np

from underworld import function as fn

from . import _convert
from . import _function

class Filter(_function.Function):

    opTag = 'Filter'

    def __init__(self, inVar, filterVal, outVar = None, **kwargs):

        inVar, filterVal = inVars = _convert.convert(
            inVar, filterVal
            )

        if outVar is None:
            outVar = inVar
        else:
            outVar = _convert.convert(outVar)
            inVars.append(outVar)
        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (fn.math.abs(inVar - filterVal) < 1e-18, nullVal),
            (True, outVar)
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)
