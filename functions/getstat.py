from underworld import function as fn

from . import _convert
from . import _reduction
from . import _basetypes
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(GetStat, *args, **kwargs)
    return func

class GetStat(_reduction.Reduction):

    opTag = 'GetStat'

    def __init__(self, inVar, *args, stat = 'mins', **kwargs):

        if not stat in {'mins', 'maxs', 'ranges'}:
            raise Exception

        inVar = _convert.convert(inVar)

        if stat == 'mins':
            var = _basetypes.Parameter(inVar.minFn)
        elif stat == 'maxs':
            var = _basetypes.Parameter(inVar.maxFn)
        elif stat == 'ranges':
            var = _basetypes.Parameter(inVar.rangeFn)

        self.stringVariants = {'stat': stat}
        self.inVars = [inVar]
        self.parameters = [var]
        self.var = var

        super().__init__(**kwargs)

def mins(*args, **kwargs):
    return construct(*args, stat = 'mins', **kwargs)

def maxs(*args, **kwargs):
    return construct(*args, stat = 'maxs', **kwargs)

def ranges(*args, **kwargs):
    return construct(*args, stat = 'ranges', **kwargs)
