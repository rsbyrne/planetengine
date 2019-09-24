import numpy as np

from underworld import function as fn

from . import _function
from . import _basetypes
from . import _convert
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Range, *args, **kwargs)
    return func

class Range(_function.Function):

    opTag = 'Range'

    def __init__(self, inVar0, inVar1, *args, operation = None, **kwargs):

        if not operation in {'in', 'out'}:
            raise Exception

        inVar0, inVar1 = inVars = \
            _convert.convert(inVar0), _convert.convert(inVar1)

        nullVal = [np.nan for dim in range(inVar0.varDim)]
        if operation == 'in':
            inVal = inVar0
            outVal = nullVal
        else:
            inVal = nullVal
            outVal = inVar0
        lowerBounds = _basetypes.Parameter(inVars[1].minFn)
        upperBounds = _basetypes.Parameter(inVars[1].maxFn)
        var = fn.branching.conditional([
            (inVar0 < lowerBounds, outVal),
            (inVar0 > upperBounds, outVal),
            (True, inVal),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = list(inVars)
        self.parameters = [lowerBounds, upperBounds]
        self.var = var

        super().__init__(**kwargs)

def inrange(*args, **kwargs):
    return construct(*args, operation = 'in', **kwargs)

def outrange(*args, **kwargs):
    return construct(*args, operation = 'out', **kwargs)
