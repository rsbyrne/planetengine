from underworld import function as fn

from . import _convert
from . import _function

class Component(_function.Function):

    opTag = 'Component'

    def __init__(self, inVar, *args, component = 'mag', **kwargs):

        inVar = _convert.convert(inVar)

        if not inVar.varDim == inVar.mesh.dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            var = fn.math.sqrt(
                fn.math.dot(
                    inVar,
                    inVar
                    )
                )
        else:
            compVec = inVar.meshUtils.comps[component]
            var = fn.math.dot(
                inVar,
                compVec
                )

        self.stringVariants = {'component': component}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def mag(*args, **kwargs):
        return Component(*args, component = 'mag', **kwargs)

    def x(*args, **kwargs):
        return Component(*args, component = 'x', **kwargs)

    def y(*args, **kwargs):
        return Component(*args, component = 'y', **kwargs)

    def z(*args, **kwargs):
        return Component(*args, component = 'z', **kwargs)

    @staticmethod
    def rad(*args, **kwargs):
        return Component(*args, component = 'rad', **kwargs)

    @staticmethod
    def ang(*args, **kwargs):
        return Component(*args, component = 'ang', **kwargs)

    @staticmethod
    def coang(*args, **kwargs):
        return Component(*args, component = 'coang', **kwargs)
