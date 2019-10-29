from underworld import function as _fn

from . import _convert
from . import _function
from ._construct import _construct as _master_construct

def _construct(*args, **kwargs):
    func = _master_construct(Component, *args, **kwargs)
    return func

class Component(_function.Function):

    opTag = 'Component'

    def __init__(self, inVar, *args, component = 'mag', **kwargs):

        inVar = _convert.convert(inVar)

        if not inVar.varDim == inVar.mesh.dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            var = _fn.math.sqrt(
                _fn.math.dot(
                    inVar,
                    inVar
                    )
                )
        else:
            compVec = inVar.meshUtils.comps[component]
            var = _fn.math.dot(
                inVar,
                compVec
                )

        self.stringVariants = {'component': component}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return _construct(*args, **kwargs)

def mag(*args, **kwargs):
    return _construct(*args, component = 'mag', **kwargs)

def x(*args, **kwargs):
    return _construct(*args, component = 'x', **kwargs)

def y(*args, **kwargs):
    return _construct(*args, component = 'y', **kwargs)

def z(*args, **kwargs):
    return _construct(*args, component = 'z', **kwargs)

def rad(*args, **kwargs):
    return _construct(*args, component = 'rad', **kwargs)

def ang(*args, **kwargs):
    return _construct(*args, component = 'ang', **kwargs)

def coang(*args, **kwargs):
    return _construct(*args, component = 'coang', **kwargs)
