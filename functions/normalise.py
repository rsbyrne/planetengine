from . import _function
from . import _convert
from . import _basetypes
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Normalise, *args, **kwargs)
    return func

class Normalise(_function.Function):

    opTag = 'Normalise'

    def __init__(self, baseVar, normVar, *args, **kwargs):

        baseVar, normVar = inVars = _convert.convert(baseVar, normVar)

        inMins = _basetypes.Parameter(baseVar.minFn)
        inRanges = _basetypes.Parameter(baseVar.rangeFn)
        normMins = _basetypes.Parameter(normVar.minFn)
        normRanges = _basetypes.Parameter(normVar.rangeFn)

        var = (baseVar - inMins) / inRanges * normRanges + normMins

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = [inMins, inRanges, normMins, normRanges]
        self.var = var

        super().__init__(**kwargs)
