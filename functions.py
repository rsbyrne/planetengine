import numpy as np
import underworld as uw
from underworld import function as fn

from .projection import get_meshVar
from .meshutils import get_meshUtils
from .utilities import unpack_var
from .utilities import hash_var
from .mapping import unbox
from .shapes import interp_shape

def make_planetVar(var):
    return Pass(var)

def _updater(self):
    def wrapper(updateFunc):
        if len(self.inheritedUpdates):
            currenthash = self.gethash()
            if not currenthash == self.lasthash:
                for inheritedUpdate in self.inheritedUpdates:
                    inheritedUpdate()
                updateFunc()
                self.lasthash = currenthash
    return wrapper

class _PlanetVar:

    def __init__(self, *args, opTag = ''):
        self.varDicts = {}
        self.inVars = []
        self.inTags = []
        self.inheritedUpdates = []
        for arg in args:
            if isinstance(arg, _PlanetVar):
                inVar = arg.var
                inTag = arg.opTag
                varDict = unpack_var(inVar, detailed = True)
                self.inheritedUpdates.append(arg.update)
            else:
                varDict = unpack_var(arg, detailed = True)
                inVar = varDict['var']
                inTag = varDict['name']
            self.inVars.append(inVar)
            self.varDicts[inVar] = varDict
            self.inTags.append(inTag)
        self.inVars = tuple(self.inVars)
        if len(self.inVars) == 1:
            self.inVar = self.inVar
            self.varDict = self.varDicts[self.inVar]
        self.var = None
        self.lasthash = 0.
        self.gethash = lambda: hash_var(self.inVars)
        self.opTag = opTag + '{' + ';'.join(self.inTags) + '}'

    @_updater
    def update(self):
        pass

    def __call__(self):
        self.update()
        return self.var

class Pass(_PlanetVar):
    def __init__(self, inVar):
        super().__init__(inVar)
        self.var = self.inVar
        self.opTag = self.opTag[1:-1] + '{}'

class Projection(_PlanetVar):

    def __init__(self, inVar):
        super().__init__(inVar, opTag = 'Projection')
        varDim = self.varDict['varDim']
        mesh = self.varDict['mesh']
        self.projection = uw.mesh.MeshVariable(
            mesh,
            varDim,
            )
        self.projector = uw.utils.MeshVariable_Projection(
            projection,
            inVar,
            )

    @_updater
    def update(self):
        self.projector.solve()
        dType = self.varDict['dType']
        if dType in ('int', 'boolean'):
            self.projection.data[:] = np.round(
                self.projection.data
                )

class Operations(_PlanetVar):

    opDict = {
        'abs': fn.math.abs,
        'cosh': fn.math.cosh,
        'acosh': fn.math.acosh,
        'tan': fn.math.tan,
        'asin': fn.math.asin,
        'log': fn.math.log,
        'atanh': fn.math.atanh,
        'sqrt': fn.math.sqrt,
        'abs': fn.math.abs,
        'log10': fn.math.log10,
        'sin': fn.math.sin,
        'asinh': fn.math.asinh,
        'log2': fn.math.log2,
        'atan': fn.math.atan,
        'sinh': fn.math.sinh,
        'cos': fn.math.cos,
        'tanh': fn.math.tanh,
        'erf': fn.math.erf,
        'erfc': fn.math.erfc,
        'exp': fn.math.exp,
        'acos': fn.math.acos,
        'dot': fn.math.dot
        }

    def __init__(self, operation, inVars):
        if not operation in self.opDict:
            raise Exception
        super().__init__(*inVars, opTag = 'Operation_' + operation)
        opFn = opDict[operation]
        self.var = opFn(*self.inVars)

class Component(_PlanetVar):

    def __init__(self, component, inVar):
        super().__init__(inVar, opTag = 'Component_' + component)
        inVar = self.inVar
        varDict = self.varDict
        if not varDict['varDim'] == varDict['mesh'].dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            self.var = fn.math.sqrt(fn.math.dot(inVar, inVar))
        else:
            meshUtils = get_meshUtils(varDict['mesh'])
            self.var = fn.math.dot(inVar, meshUtils.comps[component])

class Gradient(_PlanetVar):

    def __init__(self, gradient, inVar):
        inVarType = unpack_var(inVar, detailed = True)['varType']
        if not inVarType == 'meshVar':
            inVar = Projection(inVar)
        super().__init__(inVar, opTag = 'Gradient_' + gradient)
        inVar = self.inVar
        varDict = self.varDict
        meshVar = inVar # Projector tracking???
        varGrad = meshVar.fn_gradient
        if gradient == 'mag':
            self.var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
        else:
            meshUtils = get_meshUtils(varDict['mesh'])
            self.var = fn.math.dot(varGrad, meshUtils.comps[gradient])

class Bucket(_PlanetVar):

    def __init__(self, bucket, inVar):
        if type(bucket) is tuple:
            adjBucket = list(bucket)
            if bucket[0] == '.':
                adjBucket[0] = 1e-18
            if bucket[1] == '.':
                adjBucket[1] = 1e18
            bucketStr = str(bucket[0]) + ':' + str(bucket[1])
        else:
            adjBucket = (bucket - 1e-18, bucket + 1e-18)
            bucketStr = str(bucket)
        super().__init__(inVar, opTag = 'Bucket_' + bucketStr)
        inVar = self.inVar
        self.var = fn.branching.conditional([
            (inVar < adjBucket[0], np.nan),
            (inVar > adjBucket[1], np.nan), # double-open interval - is this a problem?
            (True, inVar),
            ])

class Quantile(_PlanetVar):

    def __init__(self, ntiles, nthtile, inVar):
        super().__init__(inVar, opTag = 'Quantile_' + quantileStr)
        inVar = self.inVar
        self.lowerBound = fn.misc.constant(0.)
        self.upperBound = fn.misc.constant(0.)
        self.ntiles = ntiles
        self.nthtile = nthtile
        l_adj = -1e-18
        if nthtile == ntiles:
            u_adj = -1e-18
        else:
            u_adj = 1e-18
        self.var = fn.branching.conditional([
            (inVar < lowerBound + l_adj, np.nan),
            (inVar > upperBound + u_adj, np.nan),
            (True, inVar),
            ])

    @_updater
    def update(self):
        intervalSize = self.varDict['ranges'] / self.ntiles
        lowerBound.value = self.varDict['scales'][:,0] \
            + intervalSize * (self.nthtile - 1)
        upperBound.value = self.varDict['scales'][:,0] \
            + intervalSize * (self.nthtile)

class Substitute(_PlanetVar):

    def __init__(self, fromVal, toVal, inVar):
        super().__init__(
            inVar,
            opTag = 'Substitute_' + str(fromVal) + ':' + str(toVal)
            )
        self.var = fn.branching.conditional([
            (fn.math.abs(self.inVar - fromVal) < 1e-18, toVal),
            (True, self.inVar),
            ])

class Binarise(_PlanetVar):

    def __init__(self, inVar):
        super().__init__(inVar, opTag = 'Binarise_')
        self.var = 0. * self.inVar + fn.branching.conditional([
            (fn.math.abs(self.inVar) < 1e-18, 0.),
            (True, 1.),
            ])

class Booleanise(_PlanetVar):

    def __init__(self, inVar):
        super().__init__(inVar, opTag = 'Booleanise_')
        self.var = 0. * self.inVar + fn.branching.conditional([
            (fn.math.abs(self.inVar) < 1e-18, False),
            (True, True),
            ])

class HandleNaN(_PlanetVar):

    def __init__(self, handleVal, inVar):
        super().__init__(
            inVar,
            'HandleNaN_' + str(handleVal)
            )
        self.var = fn.branching.conditional([
            (self.inVar < np.inf, inVar),
            (True, handleVal),
            ])

class Region(_PlanetVar):

    def __init__(self, region_name, inShape, inVar):
        super().__init__(
            inVar,
            'Region_' + region_name
            )
        inShape = interp_shape(inShape)
        inShape = unbox(self.varDict['mesh'], inShape)
        polygon = fn.shape.Polygon(inShape)
        self.var = fn.branching.conditional([
            (polygon, inVar),
            (True, np.nan),
            ])

class Integrate(_PlanetVar):

    def __init__(self, surface, inVar):
        inVarType = unpack_var(inVar, detailed = True)['varType']
        if not inVarType in {'meshVar', 'meshFn'}:
            inVar = Projection(inVar)
        super().__init__(
            inVar,
            'Integrate_' + surface
            )
        meshUtils = get_meshUtils(self.varDict['mesh'])
        self.intMesh = meshUtils.integrals[surface]
        if surface == 'volume':
            self.intField = uw.utils.Integral(self.inVar, self.varDict['mesh'])
        else:
            indexSet = meshUtils.surfaces[surface]
            self.intField = uw.utils.Integral(
                self.inVar,
                self.varDict['mesh'],
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
        self.var = fn.misc.constant(0.)

    @_updater
    def update(self):
        self.var.value = self.intField.evaluate()[0] / self.intMesh()
