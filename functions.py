import functools
import itertools
import weakref

import numpy as np
import underworld as uw
from underworld import function as fn
from underworld.function._function import Function as UWFn

from . import utilities

from .meshutils import get_meshUtils
from .mapping import unbox
from .shapes import interp_shape

# Some important universal attributes:

uwNamesToFns = {
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
uwFnsToNames = {
    val: key \
    for key, val in uwNamesToFns.items()
    }

uwNamesToDataObj = {
    'Constant': fn.misc.constant,
    'MeshVar': uw.mesh._meshvariable.MeshVariable,
    'SwarmVar': uw.swarm._swarmvariable.SwarmVariable,
    }
uwDataObjToNames = {
    val: key \
    for key, val in uwNamesToDataObj.items()
    }

def convert(var, varName = None):
    if isinstance(var, PlanetVar):
        return var
    elif hasattr(var, 'planetVar'):
        return var.planetVar
    else:
        var = UWFn.convert(var)
        if var is None:
            raise Exception
        if varName is None:
            var = Constant(var)
        else:
            var = Variable(var, varName)
        return var

get_planetVar = convert

def multi_convert(*args):
    all_converted = []
    for arg in args:
        if type(arg) == tuple:
            var, varName = arg
        else:
            var = arg, varName = None
        converted = convert(var, varName)
        all_converted.append(converted)
    return all_converted

class PlanetVar(UWFn):

    inVars = []
    opTag = 'None'

    def __init__(self):

        if type(self) in {Constant, Variable}:
            _argument_fns = [self.var]
        else:
            inTags = [inVar.varName for inVar in self.inVars]
            self.varName = self.opTag + '{' + ';'.join(inTags) + '}'
            _argument_fns = [*self.inVars]
        self._fncself = self.var._fncself
        super().__init__(_argument_fns)

        # if not hasattr(self, '_underlyingDataItems'):
        #     self.var._underlyingDataItems = weakref.WeakSet()

        if len(self.inVars) == 1:
            self.inVar = self.inVars[0]

        # self._set_underlyingDataItems()

        self._set_attributes()

        self._get_summary_stats()

        # CIRCULAR REFERENCE
        self.var.planetVar = self

    def update(self):
        pass

    def full_update(self, *args, **kwargs):
        bool_check, checked = self._check_hash(
            *args,
            **kwargs
            )
        if not bool_check:
            for inVar in self.inVars:
                inVar.full_update(
                    checked = checked,
                    *args,
                    **kwargs
                    )
            self.update()
            self._get_summary_stats()

    def _check_hash(
            self,
            checked = {},
            *args,
            **kwargs
            ):
        if not hasattr(self, 'lasthash'):
            self.lasthash = 0
        currenthash, checked = utilities.hash_var(
            self,
            checked = checked,
            global_eval = False,
            return_checked = True,
            *args,
            **kwargs
            )
        boolcheck = bool(
            uw.mpi.comm.allreduce(
                self.lasthash - currenthash
                )
            )
        self.lasthash = currenthash
        return boolcheck, checked

    # def _set_underlyingDataItems(self):
    #
    #     var = self.var
    #     inVars = self.inVars
    #
    #     if not hasattr(self, '_underlyingDataItems'):
    #         var._underlyingDataItems = weakref.WeakSet()
    #
    #     for inVar in inVars:
    #         var._underlyingDataItems.union(
    #             inVar._underlyingDataItems
    #             )
    #
    #     self._underlyingDataItems = \
    #         var._underlyingDataItems

    def _set_attributes(self):

        var = self.var

        mesh, substrate = utilities.get_substrates(
            self
            )

        if type(var) == fn.misc.constant:
            varType = 'constant'
        else:
            if type(var) == uw.swarm._swarmvariable.SwarmVariable:
                varType = 'swarmVar'
            elif type(var) == uw.mesh._meshvariable.MeshVariable:
                varType = 'meshVar'
            else:
                if substrate is mesh:
                    varType = 'meshFn'
                else:
                    varType = 'swarmFn'

        # POTENTIALLY SLOW
        data = var.evaluate(substrate)
        varDim = data.shape[1]

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

        if not mesh is None:
            meshUtils = get_meshUtils(mesh)
        else:
            meshUtils = None

        self.mesh = mesh
        self.substrate = substrate
        self.varType = varType
        self.varDim = varDim
        self.dType = dType
        self.meshUtils = meshUtils

    def _get_summary_stats(self):
        data = self.evaluate(self.substrate)
        valSets = utilities.get_valSets(data)
        if self.dType == 'double':
            scales = utilities.get_scales(
                data,
                valSets
                )
            ranges = utilities.get_ranges(
                data,
                scales
                )
            self.scales = scales
            self.ranges = ranges
        self.data = data
        self.valSets = valSets

    def evaluate(self, evalInput = None):
        self.full_update()
        if evalInput == None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def __call__(self):
        self.full_update()
        return self.var

    def __hash__(self):
        if len(self.inVars) > 0:
            selfhash = sum(
                [inVar.__hash__() for inVar in self.inVars]
                )
        else:
            selfhash = self.var.__hash__() + hash(self.varName)
        return selfhash

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

class Constant(PlanetVar):

    opTag = 'Constant'

    def __init__(self, inVar):

        var = UWFn.convert(inVar)
        if not type(var) == fn.misc.constant:
            raise Exception

        valString = utilities.stringify(
            var.value
            )
        self.varName = self.opTag + '{' + valString + '}'

        self.opTag += ''
        self.inVars = []
        self.var = var

        super().__init__()

class Variable(PlanetVar):

    opTag = 'Variable'

    def __init__(self, inVar, varName):

        var = UWFn.convert(inVar)

        self.varName = self.opTag + '{' + varName + '}'

        self.opTag += ''
        self.inVars = []
        self.var = var

        super().__init__()

class Projection(PlanetVar):

    opTag = 'Projection'

    def __init__(self, inVar):

        inVar = convert(inVar)

        var = uw.mesh.MeshVariable(
            inVar.mesh,
            inVar.varDim,
            )
        self._projector = uw.utils.MeshVariable_Projection(
            var,
            inVar.var,
            )

        self.opTag += ''
        self.inVars = [inVar]
        self.var = var

        super().__init__()

    def update(self):
        self._projector.solve()
        if self.inVar.dType in ('int', 'boolean'):
            self.var.data[:] = np.round(
                self.var.data
                )

class Operations(PlanetVar):

    opTag = 'Operation'

    def __init__(self, operation, *args):

        if not operation in uwNamesToFns:
            raise Exception
        opFn = uwNamesToFns[operation]

        var = opFn(*args)

        self.opTag += '_' + operation
        self.inVars = [convert(arg) for arg in args]
        self.var = var

        super().__init__()

class Clip(PlanetVar):

    opTag = 'Clip'

    def __init__(self, inVar, lBnd, uBnd):

        inVar, lBnd, uBnd = inVars = [
            convert(arg) for arg in (inVar, lBnd, uBnd)
            ]

        var = fn.branching.conditional([
            (inFn < lBnd, lBnd),
            (inFn > uBnd, uBnd),
            (True, inFn)
            ])

        self.opTag += ''
        self.inVars = inVars
        self.var = var

        super().__init__()

# class Normalise(PlanetVar):
#
#     def __init__(self, inVar, lBnd = 0., uBnd = 1.

class Component(PlanetVar):

    opTag = 'Component'

    def __init__(self, component, inVar):

        inVar = convert(inVar)

        if not inVar.varDim == inVar.mesh.dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            var = fn.math.sqrt(
                fn.math.dot(
                    inVar.var,
                    inVar.var
                    )
                )
        else:
            compVec = inVar.meshUtils.comps[component]
            var = fn.math.dot(
                inVar.var,
                compVec
                )

        self.opTag += ''
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Gradient(PlanetVar):

    opTag = 'Gradient'

    def __init__(self, gradient, inVar):
        inVar = convert(inVar)
        if not inVar.varType == 'meshVar':
            inVar = Projection(inVar)
        varGrad = inVar.var.fn_gradient
        if gradient == 'mag':
            var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
        else:
            compVec = inVar.meshUtils.comps[gradient]
            var = fn.math.dot(
                varGrad,
                compVec
                )

        self.opTag += '_' + gradient
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Comparison(PlanetVar):

    opTag = 'Comparison'

    def __init__(self, operation, inVar0, inVar1):

        if not operation in {'equals', 'notequals'}:
            raise Exception

        inVar0, inVar1 = inVars = convert(inVar0), convert(inVar1)
        boolOut = operation == 'equals'
        var = fn.branching.conditional([
            (inVar0.var < inVar1.var - 1e-18, not boolOut),
            (inVar0.var > inVar1.var + 1e-18, not boolOut),
            (True, boolOut),
            ])

        self.opTag += '_' + operation
        self.inVars = inVars
        self.var = var

        super().__init__()

class Bucket(PlanetVar):

    opTag = 'Bucket'

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

        inVar = convert(inVar)
        var = fn.branching.conditional([
            (inVar.var < adjBucket[0], np.nan),
            (inVar.var > adjBucket[1], np.nan),
            (True, inVar.var),
            ])

        self.opTag += '_' + bucketStr
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Range(PlanetVar):

    opTag = 'Range'

    def __init__(self, operation, inVar0, inVar1):

        if not operation in {'in', 'out'}:
            raise Exception

        inVar0, inVar1 = inVars = convert(inVar0), convert(inVar1)
        if operation == 'in':
            inVal = inVar0.var
            outVal = np.nan
        else:
            inVal = np.nan
            outVal = inVar0.var
        self._lowerBounds = fn.misc.constant(0.)
        self._upperBounds = fn.misc.constant(0.)
        var = fn.branching.conditional([
            (inVar0.var < self._lowerBounds, outVal),
            (inVar0.var > self._upperBounds, outVal),
            (True, inVal),
            ])

        self.opTag += '_' + operation
        self.inVars = inVars
        self.var = var

        super().__init__()

    def update(self):
        self._lowerBound.value = self.inVars[1].scales[:,0]
        self._upperBound.value = self.inVars[1].scales[:,1]

class Quantile(PlanetVar):

    opTag = 'Quantile'

    def __init__(self, ntiles, nthtile, inVar):

        quantileStr = str(nthtile) + "of" + str(ntiles)

        inVar = convert(inVar)

        self._lowerBound = fn.misc.constant(0.)
        self._upperBound = fn.misc.constant(0.)
        self._ntiles = ntiles
        self._nthtile = nthtile
        l_adj = -1e-18
        if nthtile == ntiles:
            u_adj = -1e-18
        else:
            u_adj = 1e-18
        var = fn.branching.conditional([
            (inVar.var < self._lowerBound + l_adj, np.nan),
            (inVar.var > self._upperBound + u_adj, np.nan),
            (True, inVar.var),
            ])

        self.opTag += '_' + quantileStr
        self.inVars = [inVar]
        self.var = var

        super().__init__()

    def update(self):
        intervalSize = self.inVar.ranges / self._ntiles
        self._lowerBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self._nthtile - 1)
        self._upperBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self._nthtile)

class Substitute(PlanetVar):

    opTag = 'Substitute'

    def __init__(self, fromVal, toVal, inVar):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (fn.math.abs(inVar.var - fromVal) < 1e-18, toVal),
            (True, inVar.var),
            ])

        self.opTag += '_' + str(fromVal) + ':' + str(toVal)
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Binarise(PlanetVar):

    opTag = 'Binarise'

    def __init__(self, inVar):

        inVar = convert(inVar)

        if inVar.dType == 'double':
            var = 0. * inVar.var + fn.branching.conditional([
                (fn.math.abs(inVar.var) > 1e-18, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'boolean':
            var = 0. * inVar.var + fn.branching.conditional([
                (inVar.var, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'int':
            var = 0 * inVar.var + fn.branching.conditional([
                (inVar.var, 1),
                (True, 0),
                ])

        self.opTag += ''
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Booleanise(PlanetVar):

    opTag = 'Booleanise'

    def __init__(self, inVar):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (fn.math.abs(inVar.var) < 1e-18, False),
            (True, True),
            ])

        self.opTag += ''
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class HandleNaN(PlanetVar):

    opTag = 'HandleNaN'

    def __init__(self, handleVal, inVar):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (inVar.var < np.inf, inVar.var),
            (True, handleVal),
            ])

        self.opTag += '_' + str(handleVal)
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Region(PlanetVar):

    opTag = 'Region'

    def __init__(self, region_name, inShape, inVar):

        inVar = convert(inVar)

        inShape = interp_shape(inShape)
        inShape = unbox(inVar.mesh, inShape)
        polygon = fn.shape.Polygon(inShape)
        var = fn.branching.conditional([
            (polygon, inVar.var),
            (True, np.nan),
            ])

        self.opTag += '_' + region_name
        self.inVars = [inVar]
        self.var = var

        super().__init__()

class Integrate(PlanetVar):

    opTag = 'Integrate'

    def __init__(self, surface, inVar):

        inVar = convert(inVar)

        if not inVar.varType in {'meshVar', 'meshFn'}:
            inVar = Projection(inVar)
        intMesh = inVar.meshUtils.integrals[surface]
        if surface == 'volume':
            intField = uw.utils.Integral(
                inVar.var,
                inVar.mesh
                )
        else:
            indexSet = inVar.meshUtils.surfaces[surface]
            intField = uw.utils.Integral(
                inVar.var,
                inVar.mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )

        var = fn.misc.constant(0.)
        self._intField = intField
        self._intMesh = intMesh

        self.opTag += '_' + surface
        self.inVars = [inVar]
        self.var = var

        super().__init__()

    def update(self):
        self.var.value = \
            self._intField.evaluate()[0] \
            / self._intMesh()
