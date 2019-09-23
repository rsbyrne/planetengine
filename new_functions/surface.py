import numpy as np

from . import _function
from . import _convert
from . import _construct

def construct():
    func = _construct(Surface, *args, **kwargs)
    return func

class Surface(_function.Function):

    opTag = 'Surface'

    def __init__(self, inVar, *args, surface = 'inner', **kwargs):

        inVar = _convert.convert(inVar)

        if inVar.substrate is None:
            raise Exception
        if not hasattr(inVar, 'mesh'):
            raise Exception

        self._surface = \
            inVar.mesh.meshUtils.surfaces[surface]

        var = inVar.mesh.add_variable(
            inVar.varDim,
            inVar.dType
            )

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self.var.data[:] = \
            [np.nan for dim in range(self.inVar.varDim)]
        self.var.data[self._surface] = \
            np.round(
                self.inVar.evaluate(
                    self.inVar.mesh.data[self._surface],
                    lazy = True
                    ),
                6
                )

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
