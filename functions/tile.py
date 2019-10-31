import numpy as np

from underworld import function as _fn

from . import _function
from . import _convert
from ._construct import _construct as _master_construct
from .. import fieldops

def _construct(*args, **kwargs):
    func = _master_construct(Tile, *args, **kwargs)
    return func

class Tile(_function.Function):

    opTag = 'Tile'

    def __init__(self, inVar, freqs, mirrored, *args, **kwargs):

        inVar, freqs, mirrored = inVars = _convert.convert(
            inVar,
            freqs,
            mirrored
            )

        var = inVar.mesh.add_variable(inVar.varDim)

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):

        inVar, freqs, mirrored = self.inVars
        freqs = tuple(*freqs.evaluate())
        mirrored = tuple(*mirrored.evaluate())
        fieldops.copyField(
            inVar.meshVar(),
            self.var,
            freqs = freqs,
            mirrored = mirrored
            )

def default(*args, **kwargs):
    return _construct(*args, **kwargs)
