from underworld import function as fn

from . import _convert
from . import _function
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Binarise, *args, **kwargs)
    return func

class Binarise(_function.Function):

    opTag = 'Binarise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = _convert.convert(inVar)

        if not inVar.varDim == 1:
            raise Exception

        if inVar.dType == 'double':
            var = 0. * inVar + fn.branching.conditional([
                (fn.math.abs(inVar) > 1e-18, 1.),
                (True, 0.),
                ])
        elif inVar.dType == 'boolean':
            var = 0. * inVar + fn.branching.conditional([
                (inVar, 1.),
                (True, 0.),
                ])
        elif inVar.dType == 'int':
            var = 0 * inVar + fn.branching.conditional([
                (inVar, 1),
                (True, 0),
                ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return construct(*args, **kwargs)
