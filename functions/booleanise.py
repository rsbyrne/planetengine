from underworld import function as fn

from . import _convert
from . import _function
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Booleanise, *args, **kwargs)
    return func

class Booleanise(_function.Function):

    opTag = 'Booleanise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = _convert.convert(inVar)

        if not inVar.varDim == 1:
            raise Exception

        var = fn.branching.conditional([
            (fn.math.abs(inVar) < 1e-18, False),
            (True, True),
            ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return construct(*args, **kwargs)
