import functools
import itertools

import numpy as np
import underworld as uw
from underworld import function as fn
import underworld.function._function as _Function

from .meshutils import get_meshUtils
from .utilities import hash_var
from .utilities import get_valSets
from .utilities import get_scales
from .utilities import get_ranges
from .utilities import message
from .mapping import unbox
from .shapes import interp_shape

def get_planetVar(var):
    if isinstance(var, PlanetVar):
        return var
    else:
        return Pass(var)

def unpack_var(*args, detailed = False, return_var = False):

    if len(args) == 1 and type(args[0]) == tuple:
        args = args[0]
    substrate = 'notprovided'
    if len(args) == 1:
        var = args[0]
        varName = 'anon'
    elif len(args) == 2:
        if type(args[0]) == str:
            varName, var = args
        else:
            var, substrate = args
            varName = 'anon'
    elif len(args) == 3:
        varName, var, substrate = args
    else:
        raise Exception("Input not understood.")

    constantTypes = {int, float, bool, np.ndarray}
    if type(var) in constantTypes:
        var = fn.misc.constant(var)
        substrate = None
    if type(var) == fn.misc.constant:
        substrate = None

    if substrate == 'notprovided':
        try:
            substrate = var.swarm
        except:
            try:
                substrate = var.mesh
            except:
                subVars = []
                for subVar in var._underlyingDataItems:
                    try: subVars.append(unpack_var(subVar, return_var = True))
                    except: pass
                if len(subVars) == 0:
                    substrate = None
                else:
                    subSwarms = list(set([
                        subVar[3] for subVar in subVars \
                            if subVar[1] in ('swarmVar', 'swarmFn')
                        ]))
                    if len(subSwarms) > 0:
                        assert len(subSwarms) < 2, \
                            "Multiple swarm dependencies detected: \
                            try providing a substrate manually."
                        substrate = subSwarms[0]
                    else:
                        subMeshes = list(set([
                            subVar[3] for subVar in subVars \
                                if subVar[1] in ('meshVar', 'meshFn')
                            ]))
                        for a, b in itertools.combinations(subMeshes, 2):
                            if a is b.subMesh:
                                subMeshes.pop(a)
                            elif b is a.subMesh:
                                subMeshes.pop(b)
                        assert len(subMeshes) < 2, \
                            "Multiple mesh dependencies detected: \
                            try providing a substrate manually."
                        substrate = subMeshes[0]

    data = var.evaluate(substrate)

    varDim = data.shape[1]

    try:
        mesh = substrate.mesh
    except:
        mesh = substrate

    # This is shocking and needs to be fixed:
    if type(var) == fn.misc.constant:
        varType = 'constant'
    elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
        varType = 'swarmVar'
    elif type(var) == uw.mesh._meshvariable.MeshVariable:
        varType = 'meshVar'
    elif hasattr(substrate, 'particleCoordinates'):
        varType = 'swarmFn'
    elif hasattr(var, 'evaluate_global'):
        varType = 'meshFn'
    else:
        raise Exception

    if str(data.dtype) == 'int32':
        dType = 'int'
    elif str(data.dtype) == 'float64':
        dType = 'double'
    elif str(data.dtype) == 'bool':
        dType = 'boolean'
    else:
        raise Exception(
            "Input data type not acceptable."
            )

    if detailed:
        outDict = {
            'varType': varType,
            'mesh': mesh,
            'substrate': substrate,
            'dType': dType,
            'varDim': varDim,
            'varName': varName,
            }
        if return_var:
            return var, outDict
        else:
            return outDict
    else:
        if return_var:
            return var, varType, mesh, substrate, dType, varDim
        else:
            return varType, mesh, substrate, dType, varDim

def _updater(updateFunc):
    @functools.wraps(updateFunc)
    def wrapper(self):
        if not self.hashFunc() == self.lasthash:
            for inVar in self.inVars:
                inVar.update()
            updateFunc(self)
            data = self.var.evaluate(self.substrate)
            self.valSets = get_valSets(data)
            if self.dType == 'double':
                self.scales = get_scales(data, self.valSets)
                self.ranges = get_ranges(data, self.scales)
            self.lasthash = self.hashFunc()
    return wrapper

class PlanetVar:

    def __init__(self, *args, opTag = ''):
        self.inVars = []
        self.inTags = []
        for arg in args:
            inVar = get_planetVar(arg)
            self.inVars.append(inVar)
            self.inTags.append(inVar.opTag)
        self.inVars = tuple(self.inVars)
        if len(self.inVars) == 1:
            self.inVar = self.inVars[0]
        self.lasthash = 0.
        self.opTag = opTag + '{' + ';'.join(self.inTags) + '}'
        self.valSets = None
        self.scales = None
        self.ranges = None

    def _finalise(self, var):
        substrate = 'notprovided'
        if len(self.inVars) > 0:
            inSubstrates = [inVar.substrate for inVar in self.inVars]
            if all([substrate == None for substrate in inSubstrates]):
                substrate = None
        var, varDict = unpack_var(
            var,
            substrate,
            detailed = True,
            return_var = True
            )
        self.var = var
        if not varDict['mesh'] == None:
            self.meshUtils = get_meshUtils(varDict['mesh'])
        for inVar in self.inVars:
            for underlyingVar in list(inVar.var._underlyingDataItems):
                self.var._underlyingDataItems.add(underlyingVar)
            if inVar.varType == 'constant':
                if len(list(inVar.var._underlyingDataItems)) == 0:
                    self.var._underlyingDataItems.add(inVar.var)
        self.hashFunc = lambda: hash_var(self.var)
        self.__dict__.update(varDict)
        self.update()
        # Ties stuff into underworld:
        self._argument_fns = [inVar.var for inVar in self.inVars]
        self._fncself = self.var._fncself

    @_updater
    def update(self):
        pass

    def evaluate(self, evalInput = None):
        self.update()
        if evalInput == None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def __call__(self):
        self.update()
        return self.var

    def __add__(self, other):
        return Operations('add', self, other)

    def __sub__(self, other):
        return Operations('subtract', self, other)

    def __mul__(self, other):
        return Operations('multiply', self, other)

    def __truediv__(self, other):
        return Operations('divide', self, other)

    def __gt__(self, other):
        return Operations('greater', self, other)

    def __ge__(self, other):
        return Operations('greater_equal', self, other)

    def __lt__(self, other):
        return Operations('less', self, other)

    def __le__(self, other):
        return Operations('less_equal', self, other)

    def __and__(self, other):
        return Operations('logical_and', self, other)

    def __or__(self, other):
        return Operations('logical_or', self, other)

    def __xor__(self, other):
        return Operations('logical_xor', self, other)

    def __pow__(self, other):
        return Operations('pow', self, other)

    def __eq__(self, other):
        return Comparison('equals', self, other)

    def __ne__(self, other):
        return Comparison('notequals', self, other)

class Pass(PlanetVar, UWFn):
    def __init__(self, inVar, name = 'anon'):
        super().__init__()
        var, varDict = unpack_var(
            inVar,
            detailed = True,
            return_var = True
            )
        self.opTag = name + '{}'
        super()._finalise(var)

class Projection(PlanetVar, UWFn):

    def __init__(self, inVar):
        super().__init__(
            inVar,
            opTag = 'Projection'
            )
        self.projection = uw.mesh.MeshVariable(
            self.inVar.mesh,
            self.inVar.varDim,
            )
        self.projector = uw.utils.MeshVariable_Projection(
            self.projection,
            self.inVar.var,
            )
        var = self.projection
        super()._finalise(var)

    @_updater
    def update(self):
        self.projector.solve()
        if self.inVar.dType in ('int', 'boolean'):
            self.var.data[:] = np.round(
                self.var.data
                )

class Operations(PlanetVar, UWFn):

    opDict = {
        'pow': fn.math.pow,
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
        'dot': fn.math.dot,
        'add': fn._function.add,
        'subtract': fn._function.subtract,
        'multiply': fn._function.multiply,
        'divide': fn._function.divide,
        'greater': fn._function.greater,
        'greater_equal': fn._function.greater_equal,
        'less': fn._function.less,
        'less_equal': fn._function.less_equal,
        'logical_and': fn._function.logical_and,
        'logical_or': fn._function.logical_or,
        'logical_xor': fn._function.logical_xor,
        'input': fn._function.input,
        }

    def __init__(self, operation, *args):
        if not operation in self.opDict:
            raise Exception
        super().__init__(
            *args,
            opTag = 'Operation_' + operation
            )
        opFn = self.opDict[operation]
        var = opFn(*[inVar.var for inVar in self.inVars])
        super()._finalise(var)

class Component(PlanetVar, UWFn):

    def __init__(self, component, inVar):
        super().__init__(
            inVar,
            opTag = 'Component_' + component
            )
        if not self.inVar.varDim == self.inVar.mesh.dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            var = fn.math.sqrt(
                fn.math.dot(
                    self.inVar.var,
                    self.inVar.var
                    )
                )
        else:
            var = fn.math.dot(
                self.inVar.var,
                self.inVar.meshUtils.comps[component]
                )
        super()._finalise(var)

class Gradient(PlanetVar, UWFn):

    def __init__(self, gradient, inVar):
        inVar = get_planetVar(inVar)
        if not inVar.varType == 'meshVar':
            inVar = Projection(inVar)
        super().__init__(
            inVar,
            opTag = 'Gradient_' + gradient
            )
        varGrad = self.inVar.var.fn_gradient
        if gradient == 'mag':
            var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
        else:
            var = fn.math.dot(varGrad, self.inVar.meshUtils.comps[gradient])
        super()._finalise(var)

class Comparison(PlanetVar, UWFn):

    def __init__(self, operation, inVar0, inVar1):
        if not operation in {'equals', 'notequals'}:
            raise Exception
        super().__init__(
            inVar0,
            inVar1,
            opTag = 'Comparison_' + operation
            )
        boolOut = operation == 'equals'
        inVar0, inVar1 = self.inVars
        var = fn.branching.conditional([
            (inVar0.var < inVar1.var - 1e-18, not boolOut),
            (inVar0.var > inVar1.var + 1e-18, not boolOut),
            (True, boolOut),
            ])
        super()._finalise(var)

class Bucket(PlanetVar, UWFn):

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
        super().__init__(
            inVar,
            opTag = 'Bucket_' + bucketStr
            )
        var = fn.branching.conditional([
            (self.inVar.var < adjBucket[0], np.nan),
            (self.inVar.var > adjBucket[1], np.nan),
            (True, self.inVar.var),
            ])
        super()._finalise(var)

class Range(PlanetVar, UWFn):
    def __init__(self, operation, inVar0, inVar1):
        if not operation in {'in', 'out'}:
            raise Exception
        super().__init__(
            inVar0,
            inVar1,
            opTag = 'Range_' + operation
            )
        if operation == 'in':
            inVal = self.inVars[0].var
            outVal = np.nan
        else:
            inVal = np.nan
            outVal = self.inVars[0].var
        self.lowerBounds = fn.misc.constant(0.)
        self.upperBounds = fn.misc.constant(0.)
        var = fn.branching.conditional([
            (self.inVars[0].var < self.lowerBounds, outVal),
            (self.inVars[0].var > self.upperBounds, outVal),
            (True, inVal),
            ])
        super()._finalise(var)
    @_updater
    def update(self):
        self.lowerBound.value = self.inVars[1].scales[:,0]
        self.upperBound.value = self.inVars[1].scales[:,1]

class Quantile(PlanetVar, UWFn):

    def __init__(self, ntiles, nthtile, inVar):
        quantileStr = str(nthtile) + "of" + str(ntiles)
        super().__init__(
            inVar,
            opTag = 'Quantile_' + quantileStr
            )
        self.lowerBound = fn.misc.constant(0.)
        self.upperBound = fn.misc.constant(0.)
        self.ntiles = ntiles
        self.nthtile = nthtile
        l_adj = -1e-18
        if nthtile == ntiles:
            u_adj = -1e-18
        else:
            u_adj = 1e-18
        var = fn.branching.conditional([
            (self.inVar.var < self.lowerBound + l_adj, np.nan),
            (self.inVar.var > self.upperBound + u_adj, np.nan),
            (True, self.inVar.var),
            ])
        super()._finalise(var)

    @_updater
    def update(self):
        intervalSize = self.inVar.ranges / self.ntiles
        self.lowerBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self.nthtile - 1)
        self.upperBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self.nthtile)

class Substitute(PlanetVar, UWFn):

    def __init__(self, fromVal, toVal, inVar):
        super().__init__(
            inVar,
            opTag = 'Substitute_' + str(fromVal) + ':' + str(toVal)
            )
        var = fn.branching.conditional([
            (fn.math.abs(self.inVar.var - fromVal) < 1e-18, toVal),
            (True, self.inVar.var),
            ])
        super()._finalise(var)

class Binarise(PlanetVar, UWFn):

    def __init__(self, inVar):
        super().__init__(
            inVar,
            opTag = 'Binarise'
            )
        if inVar.dType == 'double':
            var = 0. * self.inVar.var + fn.branching.conditional([
                (fn.math.abs(self.inVar.var) > 1e-18, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'boolean':
            var = 0. * self.inVar.var + fn.branching.conditional([
                (self.inVar.var, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'int':
            var = 0 * self.inVar.var + fn.branching.conditional([
                (self.inVar.var, 1),
                (True, 0),
                ])
        super()._finalise(var)

class Booleanise(PlanetVar, UWFn):

    def __init__(self, inVar):
        super().__init__(
            inVar,
            opTag = 'Booleanise'
            )
        var = fn.branching.conditional([
            (fn.math.abs(self.inVar.var) < 1e-18, False),
            (True, True),
            ])
        super()._finalise(var)

class HandleNaN(PlanetVar, UWFn):

    def __init__(self, handleVal, inVar):
        super().__init__(
            inVar,
            opTag = 'HandleNaN_' + str(handleVal)
            )
        var = fn.branching.conditional([
            (self.inVar.var < np.inf, inVar.var),
            (True, handleVal),
            ])
        super()._finalise(var)

class Region(PlanetVar, UWFn):

    def __init__(self, region_name, inShape, inVar):
        super().__init__(
            inVar,
            opTag = 'Region_' + region_name
            )
        inShape = interp_shape(inShape)
        inShape = unbox(self.inVar.mesh, inShape)
        polygon = fn.shape.Polygon(inShape)
        var = fn.branching.conditional([
            (polygon, self.inVar.var),
            (True, np.nan),
            ])
        super()._finalise(var)

class Integrate(PlanetVar, UWFn):

    def __init__(self, surface, inVar):
        inVar = get_planetVar(inVar)
        if not inVar.varType in {'meshVar', 'meshFn'}:
            inVar = Projection(inVar)
        super().__init__(
            inVar,
            opTag = 'Integrate_' + surface
            )
        self.intMesh = self.inVar.meshUtils.integrals[surface]
        if surface == 'volume':
            self.intField = uw.utils.Integral(
                self.inVar.var,
                self.inVar.mesh
                )
        else:
            indexSet = self.inVar.meshUtils.surfaces[surface]
            self.intField = uw.utils.Integral(
                self.inVar.var,
                self.inVar.mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
        var = fn.misc.constant(0.)
        super()._finalise(var)

    @_updater
    def update(self):
        self.var.value = \
            self.intField.evaluate()[0] \
            / self.intMesh()
