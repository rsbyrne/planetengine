import underworld as uw

from . import _convert
from . import _reduction
from . import _basetypes
from ._construct import _construct
from . import surface

def construct(*args, **kwargs):
    func = _construct(Integral, *args, **kwargs)
    return func

class Integral(_reduction.Reduction):

    opTag = 'Integral'

    def __init__(self, inVar, *args, surface = 'volume', **kwargs):

        if isinstance(inVar, _reduction.Reduction):
            raise Exception
        if type(inVar) == surface.Surface:
            raise Exception(
                "Surface type not accepted; try Integral.auto method."
                )

        inVar = HandleNaN.zeroes(inVar)

        intMesh = inVar.meshUtils.integrals[surface]
        if surface == 'volume':
            intField = uw.utils.Integral(
                inVar,
                inVar.mesh
                )
        else:
            indexSet = inVar.meshUtils.surfaces[surface]
            intField = uw.utils.Integral(
                inVar,
                inVar.mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )

        def int_eval():
            val = intField.evaluate()[0]
            val /= intMesh()
            return val
        var = _basetypes.Parameter(int_eval)

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.parameters = [var]
        self.var = var

        super().__init__(**kwargs)

def volume(*args, **kwargs):
    return construct(*args, surface = 'volume', **kwargs)

def inner(*args, **kwargs):
    return construct(*args, surface = 'inner', **kwargs)

def outer(*args, **kwargs):
    return construct(*args, surface = 'outer', **kwargs)

def left(*args, **kwargs):
    return construct(*args, surface = 'left', **kwargs)

def right(*args, **kwargs):
    return construct(*args, surface = 'right', **kwargs)

def front(*args, **kwargs):
    return construct(*args, surface = 'front', **kwargs)

def back(*args, **kwargs):
    return construct(*args, surface = 'back', **kwargs)

def auto(*args, **kwargs):
    inVar = _convert.convert(args[0])
    if type(inVar) == surface.Surface:
        surface = inVar.stringVariants['surface']
        inVar = inVar.inVar
    else:
        surface = 'volume'
    return construct(inVar, *args, surface = surface, **kwargs)
