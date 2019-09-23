import numpy as np

from . import _function
from . import _convert

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

    @staticmethod
    def volume(*args, **kwargs):
        return Surface(*args, surface = 'volume', **kwargs)

    @staticmethod
    def inner(*args, **kwargs):
        return Surface(*args, surface = 'inner', **kwargs)

    @staticmethod
    def outer(*args, **kwargs):
        return Surface(*args, surface = 'outer', **kwargs)

    @staticmethod
    def left(*args, **kwargs):
        return Surface(*args, surface = 'left', **kwargs)

    @staticmethod
    def right(*args, **kwargs):
        return Surface(*args, surface = 'right', **kwargs)

    @staticmethod
    def front(*args, **kwargs):
        return Surface(*args, surface = 'front', **kwargs)

    @staticmethod
    def back(*args, **kwargs):
        return Surface(*args, surface = 'back', **kwargs)
