from underworld import function as fn

from . import _convert
from . import _function
from ._construct import _construct
from . import component

def construct(*args, **kwargs):
    func = _construct(Gradient, *args, **kwargs)
    return func

class Gradient(_function.Function):

    opTag = 'Gradient'

    def __init__(self, inVar, *args, **kwargs):

        inVar = _convert.convert(inVar)
        inVar = inVar.meshVar()
        # DEBUGGING
        assert not inVar is None

        var = inVar.var.fn_gradient

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        self.scales = [['.', '.']] * inVar.mesh.dim ** 2
        self.bounds = [['.'] * inVar.mesh.dim ** 2] * inVar.varDim

        super().__init__(**kwargs)

def mag(*args, **kwargs):
    gradVar = construct(*args, **kwargs)
    return component.construct(gradVar, component = 'mag', **kwargs)

def rad(*args, **kwargs):
    gradVar = construct(*args, **kwargs)
    return component.construct(gradVar, component = 'rad', **kwargs)

def ang(*args, **kwargs):
    gradVar = construct(*args, **kwargs)
    return component.construct(gradVar, component = 'ang', **kwargs)

def coang(*args, **kwargs):
    gradVar = construct(*args, **kwargs)
    return component.construct(gradVar, component = 'coang', **kwargs)
