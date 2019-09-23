from underworld import function as fn

from . import _convert
from . import _reduction
from . import _basetypes

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

    @staticmethod
    def mins(*args, **kwargs):
        return GetStat(*args, stat = 'mins', **kwargs)

    @staticmethod
    def maxs(*args, **kwargs):
        return GetStat(*args, stat = 'maxs', **kwargs)

    @staticmethod
    def ranges(*args, **kwargs):
        return GetStat(*args, stat = 'ranges', **kwargs)
