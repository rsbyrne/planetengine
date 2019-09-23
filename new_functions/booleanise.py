from underworld import function as fn

from . import _convert
from . import _function
from . import _construct

def construct():
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
