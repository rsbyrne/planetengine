import numpy as np

from underworld import function as fn

from . import _function
from . import _convert
from . import _construct

def construct():
    func = _construct(Region, *args, **kwargs)
    return func

class Region(_function.Function):

    opTag = 'Region'

    def __init__(self, inVar, inShape, *args, **kwargs):

        inVar, inShape = inVars = _convert.convert(
            inVar,
            inShape
            )

        regionVar = inVar.mesh.add_variable(1)
        polygon = inShape.morph(inVar.mesh)
        boolFn = fn.branching.conditional([
            (polygon, 1),
            (True, 0),
            ])
        regionVar.data[:] = boolFn.evaluate(inVar.mesh)

        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (regionVar > 0., inVar),
            (True, nullVal),
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)
