import underworld as uw
from underworld import function as fn
import planetengine
from planetengine import unpack_var
from planetengine import standardise

class StandardIntegral:
    '''
    Takes Underworld variables and functions
    and a variety of options and builds
    integrals for data analysis.
    inVar: the variable to be integrate.
    - an Underworld variable or function based on a variable.
    comp: for multi-dimensional fields, choose the component
    to analyse. Defaults to the magnitude.
    - 'mag', 'ang', 'ang1', 'ang2', 'rad'.
    gradient: choose the component of the gradient to integrate,
    if any.
    - None, 'ang', 'ang1', 'ang2', 'rad', 'mag'.
    surface: choose the surface over which to integrate,
    or integrate 'volume' by default.
    - 'volume', 'outer', 'inner', 'left', 'right', 'front', 'back'.
    nonDim: optionally nondimensionalise the integral using
    another evaluable function.
    - a callable that returns a double.
    '''

    def __init__(
            self,
            inVar,
            comp = 'mag',
            gradient = None,
            surface = 'volume',
            nonDim = None,
            ):

        planetengine.message("Building integral...")

        self.inputs = locals().copy()
        del self.inputs['inVar']
        del self.inputs['self']

        self.opTag = ''

        unpacked = planetengine.unpack_var(inVar, return_dict = True)
        var = unpacked['var']
        mesh = unpacked['mesh']
        pemesh = planetengine.standardise(mesh)

        if unpacked['varDim'] == mesh.dim:
            # hence is vector
            if comp == 'mag':
                var = fn.math.sqrt(fn.math.dot(var, var))
            else:
                var = fn.math.dot(var, pemesh.comps[comp])
                self.opTag += comp + 'Comp_'
        else:
            assert unpacked['varDim'] == 1
            # hence is scalar.
            comp = 'mag'
            self.inputs['comp'] = comp

        if not gradient is None:

            var, self.project = pemesh.meshify(
                var,
                return_project = True
                )
            varGrad = var.fn_gradient
            if gradient == 'mag':
                var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
            else:
                var = fn.math.dot(pemesh.comps[gradient], varGrad)

            self.opTag += gradient + 'Grad_'

        intMesh = pemesh.integrals[surface]
        self.opTag += surface + 'Int_'
        if surface == 'volume':
            intField = uw.utils.Integral(var, mesh)
        else:
            indexSet = pemesh.surfaces[surface]
            intField = uw.utils.Integral(
                var,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )

        if nonDim is None:
            nonDim = lambda: 1.
        else:
            self.opTag += 'nd_' + nonDim.opTag + '_'

        self.val = lambda: \
            intField.evaluate()[0] \
            / intMesh() \
            / nonDim()

        self.opTag = self.opTag[:-1]

        planetengine.message("Integral built.")

    def evaluate(self):
        if hasattr(self, 'project'):
            self.project()
        val = self.val()
        return val

    def __call__(self):
        return self.evaluate()