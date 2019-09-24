from . import _function
from . import _convert
from ._construct import _construct
from . import component

def construct(*args, **kwargs):
    func = _construct(Merge, *args, **kwargs)
    return func

class Merge(_function.Function):

    opTag = 'Merge'

    def __init__(self, *args, **kwargs):

        inVars = _convert.convert(args)

        for inVar in inVars:
            if not inVar.varDim == 1:
                raise Exception

        dTypes = set([inVar.dType for inVar in inVars])
        if not len(dTypes) == 1:
            raise Exception
        dType = list(dTypes)[0]

        substrates = set([inVar.substrate for inVar in inVars])
        if not len(substrates) == 1:
            raise Exception

        substrate = list(substrates)[0]
        if substrate is None:
            raise Exception

        meshbased = all(
            [inVar.meshbased for inVar in inVars]
            )
        dimension = len(inVars)
        if meshbased:
            var = substrate.add_variable(dimension, dType)
        else:
            var = substrate.add_variable(dType, dimension)

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        for index, inVar in enumerate(self.inVars):
            self.var.data[:, index] = \
                inVar.evaluate()[:, 0]

def annulise(inVar):
    inVar = _convert.convert(inVar)
    comps = []
    comps.append(component.construct(inVar, component = 'ang'))
    comps.append(component.construct(inVar, component = 'rad'))
    if inVar.mesh.dim == 3:
        comps.append(component.construct(inVar, component = 'coang'))
    var = construct(*comps)
    return var

def cartesianise(inVar):
    inVar = _convert.convert(inVar)
    comps = []
    comps.append(component.construct(inVar, component = 'x'))
    comps.append(component.construct(inVar, component = 'y'))
    if inVar.mesh.dim == 3:
        comps.append(component.construct(inVar, component = 'z'))
    var = construct(*comps)
    return var
