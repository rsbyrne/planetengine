from underworld import function as fn

from . import _function
from . import _convert
from . import _construct

def construct():
    func = _construct(Substitute, *args, **kwargs)
    return func

class Substitute(_function.Function):

    opTag = 'Substitute'

    def __init__(self, inVar, fromVal, toVal, *args, **kwargs):

        inVar, fromVal, toVal = inVars = _convert.convert(
            inVar, fromVal, toVal
            )

        var = fn.branching.conditional([
            (fn.math.abs(inVar - fromVal) < 1e-18, toVal),
            (True, inVar),
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)
