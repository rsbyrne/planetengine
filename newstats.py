import underworld as uw
from underworld import function as fn
from planetengine import meshutils

class ScalarIntegral:

    def __init__(
            self,
            inVar,
            gradient = None,
            comp = None,
            surface = 'volume',
            nonDim = None,
            ):

        self.inputs = locals().copy()
        del self.inputs['stInp']

        self.opTag = ''

        stInp = planetengine.standards.StandardInput(inVar)
        meshUtils = stInp.meshUtils
        var = stInp.meshVar

        if not comp is None:
            if comp == 'mag':
                var = fn.math.sqrt(fn.math.dot(var, var))
            else:
                var = fn.math.dot(var, self.meshUtils.comps[comp])
            self.opTag += comp + '_'

        if not gradient is None:
            assert type(var) == uw.mesh._meshvariable.MeshVariable, \
                "Only mesh variables accepted for gradient option: \
                consider projecting your variable onto a mesh variable."
            varGrad = var.fn_gradient
            if gradient == 'mag':
                var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
            else:
                var = fn.math.dot(self.meshUtils.comps[gradient], varGrad)
            self.opTag += 'grad_' + gradient + '_'

        intMesh = self.meshUtils.integrals[surface]
        self.opTag += surface + '_'
        if surface == 'volume':
            intField = uw.utils.Integral(var, mesh)
        else:
            indexSet = self.meshUtils.surfaces[surface]
            intField = uw.utils.Integral(
                var,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
        self.opTag += 'integral_'

        if nonDim is None:
            nonDim = lambda: 1.
        else:
            self.opTag += 'nd_' + nonDim.opTag + '_'

        self.val = lambda: \
            intField.evaluate()[0] \
            / intMesh() \
            / nonDim()

        self.opTag = self.opTag[:-1]

    def evaluate(self):
        self.stInp.update()
        return self.val()

    def __call__(self):
        return self.evaluate()
