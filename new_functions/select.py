import numpy as np

from underworld import function as fn

from . import _function
from . import _convert
from . import _construct

def construct():
    func = _construct(Select, *args, **kwargs)
    return func

class Select(_function.Function):

    opTag = 'Select'

    def __init__(self, inVar, selectVal, outVar = None, **kwargs):

        inVar, selectVal = inVars = _convert.convert(
            inVar, selectVal
            )

        if outVar is None:
            outVar = inVar
        else:
            outVar = _convert.convert(outVar)
            inVars = tuple([*list(inVars), outVar])
        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (fn.math.abs(inVar - selectVal) < 1e-18, outVar),
            (True, nullVal)
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)
