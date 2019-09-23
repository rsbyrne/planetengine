from underworld import function as fn

from . import _convert
from . import _function
from . import component

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

    @staticmethod
    def mag(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return component.Component(gradVar, component = 'mag', **kwargs)

    @staticmethod
    def rad(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return component.Component(gradVar, component = 'rad', **kwargs)

    @staticmethod
    def ang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return component.Component(gradVar, component = 'ang', **kwargs)

    @staticmethod
    def coang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return component.Component(gradVar, component = 'coang', **kwargs)
