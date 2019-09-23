import underworld as uw

from . import _convert
from . import _reduction
from . import _surface
from . import _basetypes

class Integral(_reduction.Reduction):

    opTag = 'Integral'

    def __init__(self, inVar, *args, surface = 'volume', **kwargs):

        if isinstance(inVar, _reduction.Reduction):
            raise Exception
        if type(inVar) == _surface.Surface:
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

    @staticmethod
    def volume(*args, **kwargs):
        return Integral(*args, surface = 'volume', **kwargs)

    @staticmethod
    def inner(*args, **kwargs):
        return Integral(*args, surface = 'inner', **kwargs)

    @staticmethod
    def outer(*args, **kwargs):
        return Integral(*args, surface = 'outer', **kwargs)

    @staticmethod
    def left(*args, **kwargs):
        return Integral(*args, surface = 'left', **kwargs)

    @staticmethod
    def right(*args, **kwargs):
        return Integral(*args, surface = 'right', **kwargs)

    @staticmethod
    def front(*args, **kwargs):
        return Integral(*args, surface = 'front', **kwargs)

    @staticmethod
    def back(*args, **kwargs):
        return Integral(*args, surface = 'back', **kwargs)

    @staticmethod
    def auto(*args, **kwargs):
        inVar = _convert.convert(args[0])
        if type(inVar) == _surface.Surface:
            surface = inVar.stringVariants['surface']
            inVar = inVar.inVar
        else:
            surface = 'volume'
        return Integral(inVar, *args, surface = surface, **kwargs)
