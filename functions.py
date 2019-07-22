import numpy as np
import underworld as uw
from underworld import function as fn

from .projection import get_meshVar
from .meshutils import get_meshUtils
from .utilities import unpack_var
from .utilities import hash_var
from .mapping import unbox
from .shapes import interp_shape

class Updater:
    def __init__(self, inVar, updateFunc, inheritedUpdate = None):
        if inheritedUpdate is None:
            self.inheritedUpdate = lambda: None
        else:
            self.inheritedUpdate = inheritedUpdate
        self.updateFunc = updateFunc
        self.lasthash = 0.
        self.gethash = lambda: hash_var(inVar)
    def __call__(self):
        currenthash = self.gethash
        if not currenthash == self.lasthash:
            self.inheritedUpdate()
            self.updateFunc()
            self.lasthash = currenthash

def _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate):

    if opTags is None:
        opTags = ''
    opTags = opTag + '{' + opTags + '}'

    combinedUpdate = Updater(inVar, updateFunc, inheritedUpdate)

    return outVar, opTags, combinedUpdate

def operations(operation, var, opTags = None, inheritedUpdate = None):

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
    # ^^^ not all of these will work yet...
    if not operation in opDict:
        raise Exception

    opFn = opDict[operation]
    outinVar = opFn(inVar)

    opTag = 'Operation_' + operation
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def component(component, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    if not varDict['varDim'] == varDict['mesh'].dim:
        # hence is not a vector and so has no components:
        raise Exception
    if component == 'mag':
        outVar = fn.math.sqrt(fn.math.dot(inVar, inVar))
    else:
        meshUtils = get_meshUtils(varDict['mesh'])
        outVar = fn.math.dot(inVar, meshUtils.comps[component])

    opTag = 'Component_' + component
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def gradient(gradient, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    meshUtils = get_meshUtils(varDict['mesh'])
    meshVar, projectionFunc = get_meshVar(inVar)
    varGrad = meshVar.fn_gradient
    if gradient == 'mag':
        outVar = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
    else:
        outVar = fn.math.dot(varGrad, meshUtils.comps[gradient])

    opTag = 'Gradient_' + gradient
    updateFunc = projectionFunc

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def bucket(bucket, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

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

    outVar = fn.branching.conditional([
        (inVar < adjBucket[0], np.nan),
        (inVar > adjBucket[1], np.nan), # double-open interval - is this a problem?
        (True, inVar),
        ])

    opTag = 'Bucket_' + bucketStr
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def quantile(ntiles, nthtile, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    if not (type(ntiles) is int and type(nthtile) is int):
        raise Exception

    lowerBound = fn.misc.constant(0.)
    upperBound = fn.misc.constant(0.)

    def update_bounds():
        intervalSize = varDict['ranges'] / ntiles
        lowerBound.value = varDict['scales'][:,0] + intervalSize * (nthtile - 1)
        upperBound.value = varDict['scales'][:,0] + intervalSize * (nthtile)

    l_adj = -1e-18
    if nthtile == ntiles:
        u_adj = -1e-18
    else:
        u_adj = 1e-18
    outVar = fn.branching.conditional([
        (inVar < lowerBound + l_adj, np.nan),
        (inVar > upperBound + u_adj, np.nan),
        (True, inVar),
        ])

    quantileStr = str(nthtile) + 'of' + str(ntiles)
    opTag = 'Quantile_' + quantileStr
    updateFunc = update_bounds

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def substitute(fromVal, toVal, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    outVar = fn.branching.conditional([
        (fn.math.abs(inVar - fromVal) < 1e-18, toVal),
        (True, inVar),
        ])

    opTag = 'Substitute_' + str(fromVal) + ':' + str(toVal)
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def binarise(inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    outVar = 0. * inVar + fn.branching.conditional([
        (fn.math.abs(inVar) < 1e-18, 0.),
        (True, 1.),
        ])

    opTag = 'Binarise_'
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def booleanise(inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    outVar = 0. * inVar + fn.branching.conditional([
        (fn.math.abs(inVar) < 1e-18, False),
        (True, True),
        ])

    opTag = 'Booleanise_'
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def handleNaN(inVar, opTags = None, inheritedUpdate = None, handleVal = 0.):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    outVar = fn.branching.conditional([
        (inVar < np.inf, inVar),
        (True, handleVal),
        ])

    opTag = 'HandleNaN_' + str(handleVal)
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def region(region_name, inShape, inVar, opTags = None, inheritedUpdate = None):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    inShape = interp_shape(inShape)
    inShape = unbox(varDict['mesh'], inShape)

    polygon = fn.shape.Polygon(inShape)
    outVar = fn.branching.conditional([
        (polygon, inVar),
        (True, np.nan),
        ])

    opTag = 'Region_' + region_name
    updateFunc = lambda: None

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)

def integrate(inVar, opTags = None, inheritedUpdate = None, surface = 'volume'):

    varDict = unpack_var(inVar, detailed = True)
    inVar = varDict['var']

    meshUtils = get_meshUtils(varDict['mesh'])
    if varDict['varType'] in {'meshVar', 'meshFn'}:
        meshVar = inVar
        updateProjection = lambda: None
    else:
        # hence projection is needed:
        meshVar, updateProjection = get_meshVar(inVar)
    intMesh = meshUtils.integrals[surface]
    if surface == 'volume':
        intField = uw.utils.Integral(meshVar, varDict['mesh'])
    else:
        indexSet = meshUtils.surfaces[surface]
        intField = uw.utils.Integral(
            meshVar,
            varDict['mesh'],
            integrationType = 'surface',
            surfaceIndexSet = indexSet
            )
    outVar = fn.misc.constant(0.)
    def updateVal():
        updateProjection()
        outVar.value = intField.evaluate()[0] / intMesh()

    opTag = 'Integrate_' + surface
    updateFunc = updateVal

    return _return(outVar, inVar, opTag, opTags, updateFunc, inheritedUpdate)
