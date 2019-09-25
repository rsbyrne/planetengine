import numpy as np

from underworld import function as fn

from . import _convert
from . import _function
from ._construct import _construct
from . import getstat

def construct(*args, **kwargs):
    func = _construct(HandleNaN, *args, **kwargs)
    return func

class HandleNaN(_function.Function):

    opTag = 'HandleNaN'

    def __init__(self, inVar, handleVal, *args, **kwargs):

        inVar, handleVal = inVars = _convert.convert(
            inVar,
            handleVal
            )

        compareVal = [
            np.inf for dim in range(inVar.varDim)
            ]
        var = fn.branching.conditional([
            (inVar < compareVal, inVar),
            (True, handleVal),
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return construct(*args, **kwargs)

def _NaNFloat(inVar, handleFloat, **kwargs):
    inVar = _convert.convert(inVar)
    handleVal = [
        handleFloat for dim in range(inVar.varDim)
        ]
    return construct(inVar, handleVal = handleVal, **kwargs)

def zeroes(inVar, **kwargs):
    return _NaNFloat(inVar, 0., **kwargs)

def units(inVar, **kwargs):
    return _NaNFloat(inVar, 1., **kwargs)

def mins(inVar, **kwargs):
    handleVal = _getstat.GetStat.mins(inVar)
    return _NaNFloat(inVar, handleVal, **kwargs)

def maxs(inVar, **kwargs):
    handleVal = _getstat.GetStat.maxs(inVar)
    return _NaNFloat(inVar, handleVal, **kwargs)
