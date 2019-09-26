import numpy as np

import underworld as uw

from . import _function
from . import _convert
from ._construct import _construct

def construct(*args, **kwargs):
    func = _construct(Projection, *args, **kwargs)
    return func

class Projection(_function.Function):

    opTag = 'Projection'

    def __init__(self, inVar, *args, **kwargs):

        inVar = _convert.convert(inVar)

        var = uw.mesh.MeshVariable(
            inVar.mesh,
            inVar.varDim,
            )
        self._projector = uw.utils.MeshVariable_Projection(
            var,
            inVar,
            )
        self._meshVar = lambda: var

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self._projector.solve()
        allwalls = self.meshUtils.surfaces['all']
        self.var.data[allwalls.data] = \
            self.inVar.evaluate(allwalls)
        if self.inVar.dType in ('int', 'boolean'):
            rounding = 1
        else:
            rounding = 6
        self.var.data[:] = np.round(
            self.var.data,
            rounding
            )

def default(*args, **kwargs):
    return construct(*args, **kwargs)
