import numpy as np

import underworld as uw

from . import _function
from . import _convert
from ._construct import _construct as _master_construct

def _construct(*args, **kwargs):
    func = _master_construct(Projection, *args, **kwargs)
    return func

class Projection(_function.Function):

    opTag = 'Projection'

    def __init__(self, inVar, *args, **kwargs):

        inVar = _convert.convert(inVar)

        if self.inVar.dType in ('int', 'boolean'):
            rounding = 1
        else:
            rounding = 6

        var = inVar.meshUtils.meshify(
            inVar.var,
            vector = inVar.vector,
            solve = False
            )

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        self._meshVar = lambda: var

        super().__init__(**kwargs)

    def _partial_update(self):
        self.var.project()

def default(*args, **kwargs):
    return _construct(*args, **kwargs)
