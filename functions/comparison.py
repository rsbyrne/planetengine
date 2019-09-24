from underworld import function as fn

from . import _convert
from . import _function
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Comparison, *args, **kwargs)
    return func

class Comparison(_function.Function):

    opTag = 'Comparison'

    def __init__(self, inVar0, inVar1, *args, operation = 'equals', **kwargs):

        if not operation in {'equals', 'notequals'}:
            raise Exception

        inVar0, inVar1 = inVars = _convert.convert(inVar0, inVar1)
        boolOut = operation == 'equals'
        var = fn.branching.conditional([
            (inVar0 < inVar1 - 1e-18, not boolOut),
            (inVar0 > inVar1 + 1e-18, not boolOut),
            (True, boolOut),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def isequal(*args, **kwargs):
    return construct(*args, operation = 'equals', **kwargs)

def isnotequal(*args, **kwargs):
    return construct(*args, operation = 'notequals', **kwargs)
