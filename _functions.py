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

_premade_fns = {}

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

def update_opTag(opTag, stringVariants):
    for key, val in sorted(stringVariants.items()):
        opTag += '_' + str(key) + '=' + str(val)
    return opTag

def get_opHash(varClass, *inVars, stringVariants = {}):
    hashVal = 0
    if varClass is Shape:
        assert len(inVars) == 1
        vertices = inVars[0]
        hashVal += hash(
            utilities.stringify(
                vertices
                )
            )
    elif varClass is Constant:
        assert len(inVars) == 1
        var = UWFn.convert(inVars[0])
        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) > 0:
            raise Exception
        value = var.evaluate()[0]
        valString = utilities.stringify(
            value
            )
        stringVariants = {'val': valString}
    elif varClass is Variable:
        assert len(inVars) == 1
        var = UWFn.convert(inVars[0])
        hashVal += var.__hash__()
    else:
        rootVars = set()
        for inVar in inVars:
            assert isinstance(inVar, PlanetVar)
            rootVars = rootVars.union(
                rootVars,
                inVar.rootVars
                )
        for rootVar in rootVars:
            hashVal += rootVar.__hash__()
    fulltag = update_opTag(varClass.opTag, stringVariants)
    hashVal += hash(fulltag)
    return hashVal

# def _construct(
#         *inVars,
#         varClass = None,
#         stringVariants = {},
#         **kwargs
#         ):
#
#     if not varClass in {Constant, Variable, Shape}:
#         inVars = [convert(inVar) for inVar in inVars]
#
#     if varClass is Constant:
#         # constants don't get saved!!!
#         outObj = varClass(
#             *inVars,
#             **stringVariants,
#             **kwargs
#             )
#     else:
#         opHash = get_opHash(
#             varClass,
#             *inVars,
#             stringVariants = stringVariants
#             )
#         if opHash in _premade_fns:
#             print("Returning premade!")
#             outObj = _premade_fns[opHash]() # is weakref
#         else:
#             print("Making a new one!")
#             outObj = varClass(
#                 *inVars,
#                 **stringVariants,
#                 **kwargs
#                 )
#
#     return outObj

def _construct(
        *inVars,
        varClass = None,
        stringVariants = {},
        **kwargs
        ):

    outObj = varClass(
        *inVars,
        **stringVariants,
        **kwargs
        )

    return outObj

def _convert(var, *args, varName = 'anon', **kwargs):
    if isinstance(var, PlanetVar):
        return var
    # elif hasattr(var, 'planetVar'):
    #     return var.planetVar
    else:
        try:
            var = UWFn.convert(var, *args, **kwargs)
            if var is None:
                raise Exception
            if len(list(var._underlyingDataItems)) == 0:
                valString = utilities.stringify(
                    var.evaluate()[0]
                    )
                stringVariants = {'val': valString}
                var = _construct(
                    var,
                    *args,
                    varClass = Constant,
                    stringVariants = stringVariants,
                    **kwargs
                    )
            else:
                stringVariants = {'varName': varName}
                var = _construct(
                    var,
                    *args,
                    varClass = Variable,
                    stringVariants = stringVariants,
                    **kwargs
                    )
        except:
            try:
                stringVariants = {'varName': varName}
                var = _construct(
                    var,
                    *args,
                    varClass = Shape,
                    stringVariants = stringVariants,
                    **kwargs
                    )
            except:
                raise Exception
        return var

def convert(*args, return_tuple = False, **kwargs):
    if len(args) == 1:
        arg = args[0]
        if type(arg) == tuple:
            converted = _tuple_convert(arg, **kwargs)
        elif type(arg) == list:
            converted = _multi_convert(*arg, **kwargs)
        elif type(arg) == dict:
            converted = _dict_convert(arg, **kwargs)
        else:
            converted = _convert(arg, **kwargs)
    elif len(args) == 2:
        if type(args[0]) == str:
            converted = _convert(args[1], args[0], **kwargs)
        elif type(args[1]) == str:
            converted = _convert(args[0], args[1], **kwargs)
        else:
            converted = _multi_convert(*args, **kwargs)
    else:
        converted = _multi_convert(*args, **kwargs)
    if type(converted) == tuple:
        return converted
    else:
        if return_tuple:
            return (converted,)
        else:
            return converted

get_planetVar = convert

def _multi_convert(*args, **kwargs):
    all_converted = []
    for arg in args:
        all_converted.append(convert(arg, **kwargs))
    return tuple(all_converted)

def _tuple_convert(inTuple):
    var, varName = inTuple
    return _convert(var, varName)

def _dict_convert(inDict):
    all_converted = []
    for varName, var in sorted(inDict.items()):
        newVar = _convert(var, varName, **kwargs)
        all_converted.append(newVar)
    if len(all_converted) == 1:
        return all_converted[0]
    else:
        return tuple(all_converted)

def get_projection(
        inVar,
        *args,
        hide = False,
        attach = False,
        **kwargs
        ):
    inVar = convert(inVar, *args, **kwargs)
    if Projection.opTag in inVar.attached:
        outVar = inVar.attached[Projection.opTag]
    else:
        outVar = Projection(
            inVar,
            *args,
            hide = hide,
            attach = attach,
            **kwargs
            )
    return outVar

def get_meshVar(
        inVar,
        *args,
        hide = False,
        attach = False,
        **kwargs
        ):
    inVar = convert(inVar, *args, **kwargs)
    if inVar.varType == 'meshVar':
        outVar = inVar
    else:
        outVar = get_projection(
            inVar,
            *args,
            hide = hide,
            attach = attach,
            **kwargs
            )
    return outVar

class PlanetVar(UWFn):

    inVars = []
    opTag = 'None'

    def __init__(self, *args, hide = False, attach = False, **kwargs):

        # Determing inVars:

        self.inVars = list(self.inVars)
        if len(self.inVars) == 1:
            self.inVar = self.inVars[0]

        # Attaching, if necessary:

        self.attached = {}
        if attach:
            if len(self.inVars) > 1:
                raise Exception
            if self.opTag in self.inVar.attached:
                raise Exception
            # POSSIBLE CIRCULAR DEPENDENCY!!!
            self.inVar.attached[self.opTag] = self

        # Naming the variable:

        self.opTag = update_opTag(self.opTag, self.stringVariants)
        if hide:
            if len(self.inVars) > 1:
                raise Exception
            self.varName = self.inVar.varName
        else:
            inTags = [inVar.varName for inVar in self.inVars]
            self.varName = self.opTag + '{' + ';'.join(inTags) + '}'

        # Stuff to make Underworld happy:

        if type(self) in {Constant, Variable, Shape}:
            _argument_fns = [self.var]
        else:
            _argument_fns = [*self.inVars]

        self._fncself = self.var._fncself

        super().__init__(_argument_fns)

        # Other necessary business:

        self.lasthash = 0

        self._set_rootVars()

        self._set_attributes()

        self._set_summary_stats()

        if not self.__class__ is Constant:
            self._set_weakref(self) # is static

    def _set_rootVars(self):
        rootVars = set()
        if not type(self) in {Constant, Variable, Shape}:
            assert len(self.inVars) > 0
            for inVar in self.inVars:
                if isinstance(inVar, BaseTypes):
                    rootVars.add(inVar)
                else:
                    for rootVar in inVar.rootVars:
                        rootVars.add(rootVar)
        assert all(
            [type(rootVar) in {Constant, Variable, Shape} \
            for rootVar in list(rootVars)]
            )
        self.rootVars = rootVars

    def _partial_update(self):
        pass

    def update(self):
        if self._has_changed():
            for inVar in self.inVars:
                inVar.update()
            self._partial_update()
            self.data = self.var.evaluate(self.substrate)
            self._set_summary_stats()

    def _check_hash(self):
        currenthash = 0
        for inVar in self.inVars:
            currenthash += inVar._check_hash()
        return currenthash

    def _has_changed(self):
        currenthash = self._check_hash()
        has_changed = bool(
            uw.mpi.comm.allreduce(
                currenthash - self.lasthash
                )
            )
        self.lasthash = currenthash
        return has_changed

    def _set_attributes(self):

        var = self.var

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            varType = 'meshVar'
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            varType = 'swarmVar'
        elif isinstance(var, UWFn):
            varType = 'fn'
        else:
            raise Exception

        if hasattr(self, 'substrate'):
            substrate = self.substrate
        else:
            substrates = set(
                [rootVar.substrate \
                for rootVar in self.rootVars \
                if not rootVar.substrate is None]
                )
            if len(substrates) == 0:
                substrate = None
            elif len(substrates) == 1:
                substrate = list(substrates)[0]
            else:
                raise Exception

        if hasattr(self, 'mesh'):
            mesh = self.mesh
        else:
            meshes = set(
                [rootVar.mesh \
                for rootVar in self.rootVars \
                if not rootVar.mesh is None]
                )
            if len(meshes) == 0:
                mesh = None
            elif len(meshes) == 1:
                mesh = list(meshes)[0]
            else:
                raise Exception

        if type(self) == Constant:
            sample_data = np.array([[self.value]])
        elif type(self) == Shape:
            sample_data = self.vertices
        elif mesh is None:
            sample_data = var.evaluate()
        else:
            sample_data = var.evaluate(mesh.data[0:1])
        varDim = sample_data.shape[1]

        if str(sample_data.dtype) == 'int32':
            dType = 'int'
        elif str(sample_data.dtype) == 'float64':
            dType = 'double'
        elif str(sample_data.dtype) == 'bool':
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
        self.meshbased = substrate is mesh
        self.varDim = varDim
        self.dType = dType
        self.meshUtils = meshUtils
        self.varType = varType

    def _set_summary_stats(self):
        if hasattr(self, 'data'):
            data = self.data
            assert not len(data.shape) > 2
            valSets = utilities.get_valSets(data)
        else:
            data = None
            valSets = [[0] for dim in range(self.varDim)]
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
        self.valSets = valSets

    @staticmethod
    def _set_weakref(self):
        weak_reference = weakref.ref(self)
        hashKey = self.__hash__()
        _premade_fns[hashKey] = weak_reference

    def evaluate(self, evalInput = None):
        self.update()
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def __call__(self):
        self.update()
        return self

    def __hash__(self):
        if self.__class__ is Variable:
            inVars = [self.var]
        elif self.__class__ is Constant:
            inVars = [self.var]
        elif self.__class__ is Shape:
            inVars = [self.vertices]
        else:
            inVars = self.inVars
        hashVal = get_opHash(
            self.__class__,
            *inVars,
            stringVariants = self.stringVariants
            )
        return hashVal

    # def __hash__(self):
    #     selfhash = sum(
    #         [inVar.__hash__() for inVar in self.inVars]
    #         )
    #     selfhash += hash(self.opTag)
    #     return selfhash

    def __add__(self, other):
        return Operations(self, other, uwop = 'add')

    def __sub__(self, other):
        return Operations(self, other, uwop = 'subtract')

    def __mul__(self, other):
        return Operations(self, other, uwop = 'multiply')

    def __truediv__(self, other):
        return Operations(self, other, uwop = 'divide')

    def __gt__(self, other):
        return Operations(self, other, uwop = 'greater')

    def __ge__(self, other):
        return Operations(self, other, uwop = 'greater_equal')

    def __lt__(self, other):
        return Operations(self, other, uwop = 'less')

    def __le__(self, other):
        return Operations(self, other, uwop = 'less_equal')

    def __and__(self, other):
        return Operations(self, other, uwop = 'logical_and')

    def __or__(self, other):
        return Operations(self, other, uwop = 'logical_or')

    def __xor__(self, other):
        return Operations(self, other, uwop = 'logical_xor')

    def __pow__(self, other):
        return Operations(self, other, uwop = 'pow')

    # def __eq__(self, other):
    #     return Comparison(self, other, uwop = 'equals')
    #
    # def __ne__(self, other):
    #     return Comparison(self, other, uwop = 'notequals')

class BaseTypes(PlanetVar):

    def __init__(self, *args, **kwargs):
        # CIRCULAR REFERENCE
        # self.var.planetVar = self
        # self.opTag = update_opTag(
        #     self.opTag,
        #     self.stringVariants
        #     )
        super().__init__(*args, **kwargs)

    def evaluate(self, evalInput = None):
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def update(self):
        if type(self) == Constant:
            self.data = np.array([self.value,])
        elif type(self) == Shape:
            self.data = self.vertices
        elif hasattr(self.var, 'data'):
            self.data = self.var.data
        else:
            # i.e. is a function
            self.data = self.var.evaluate(self.substrate)
        self._set_summary_stats()

    def __call__(self):
        return self.var

class Constant(BaseTypes):

    opTag = 'Constant'

    def __init__(self, inVar, *args, **kwargs):

        var = UWFn.convert(inVar)
        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) > 0:
            raise Exception

        self.value = var.evaluate()[0]
        valString = utilities.stringify(
            self.value
            )

        self.stringVariants = {'val': valString}
        self.inVars = []
        self.var = var
        self.mesh = self.substrate = None

        super().__init__(*args, **kwargs)

    def _check_hash(self):
        currenthash = hash(utilities.stringify(self.value))
        return currenthash

class Variable(BaseTypes):

    opTag = 'Variable'

    def __init__(self, inVar, varName = 'anon', *args, **kwargs):

        var = UWFn.convert(inVar)
        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) == 0:
            raise Exception

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.var = var
        if hasattr(var, 'fn_gradient'):
            self.fn_gradient = var.fn_gradient
        try:
            self.mesh = var.mesh
            self.substrate = self.mesh
        except:
            try:
                self.substrate = var.swarm
                self.mesh = self.substrate.mesh
            except:
                self.mesh, self.substrate = \
                    utilities.get_substrates(var)

        super().__init__(*args, **kwargs)

    def _check_hash(self):
        self.update() # resets self.data
        currenthash = hash(utilities.stringify(self.data))
        return currenthash

class Shape(BaseTypes):

    opTag = 'Shape'

    def __init__(self, vertices, varName = 'anon', *args, **kwargs):

        shape = fn.shape.Polygon(vertices)
        self.vertices = vertices
        self.richvertices = interp_shape(self.vertices)
        self.morphs = {}

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.var = shape
        self.mesh = self.substrate = None

        super().__init__(*args, **kwargs)

    def _check_hash(self):
        currenthash = hash(utilities.stringify(self.vertices))
        return currenthash

    def morph(self, mesh):
        try:
            morphpoly = self.morphs[mesh]
        except:
            morphverts = unbox(mesh, self.richvertices)
            morphpoly = fn.shape.Polygon(morphverts)
            self.morphs[mesh] = morphpoly
        return morphpoly

class Utils(PlanetVar):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

class Projection(Utils):

    opTag = 'Projection'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        var = uw.mesh.MeshVariable(
            inVar.mesh,
            inVar.varDim,
            )
        self._projector = uw.utils.MeshVariable_Projection(
            var,
            inVar,
            )

        self.stringVariants = {}
        self.inVars = [inVar]
        self.var = var

        self.fn_gradient = var.fn_gradient

        super().__init__(*args, **kwargs)

    def _partial_update(self):
        self._projector.solve()
        if self.inVar.dType in ('int', 'boolean'):
            self.var.data[:] = np.round(
                self.var.data
                )

class Substitute(Utils):

    opTag = 'Substitute'

    def __init__(self, inVar, fromVal, toVal, *args, **kwargs):

        inVar, fromVal, toVal = inVars = convert(
            inVar, fromVal, toVal
            )

        var = fn.branching.conditional([
            (fn.math.abs(inVar - fromVal) < 1e-18, toVal),
            (True, inVar),
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

class Binarise(Utils):

    opTag = 'Binarise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        if inVar.dType == 'double':
            var = 0. * inVar + fn.branching.conditional([
                (fn.math.abs(inVar) > 1e-18, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'boolean':
            var = 0. * inVar + fn.branching.conditional([
                (inVar, 1.),
                (True, 0.),
                ])
        elif invar.dType == 'int':
            var = 0 * inVar + fn.branching.conditional([
                (inVar, 1),
                (True, 0),
                ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

class Booleanise(Utils):

    opTag = 'Booleanise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (fn.math.abs(inVar) < 1e-18, False),
            (True, True),
            ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

class HandleNaN(Utils):

    opTag = 'HandleNaN'

    def __init__(self, handleVal, inVar, *args, **kwargs):

        inVar, handleVal = inVars = convert(inVar, handleVal)

        var = fn.branching.conditional([
            (inVar < np.inf, inVar),
            (True, handleVal),
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

class ZeroNaN(Utils):

    opTag = 'ZeroNaN'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (inVar < np.inf, inVar),
            (True, 0.),
            ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

class Functions(PlanetVar):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

class Clip(Functions):

    opTag = 'Clip'

    def __init__(self, inVar, lBnd, uBnd, *args, **kwargs):

        inVar, lBnd, uBnd = inVars = [
            convert(arg) for arg in (inVar, lBnd, uBnd)
            ]

        var = fn.branching.conditional([
            (inFn < lBnd, lBnd),
            (inFn > uBnd, uBnd),
            (True, inFn)
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

class Interval(Functions):

    opTag = 'Interval'

    def __init__(self, inVar, lBnd, uBnd, *args, **kwargs):

        inVar, lBnd, uBnd = inVars = convert(inVar, lBnd, uBnd)

        inVar = convert(inVar)
        var = fn.branching.conditional([
            (inVar <= lBnd, np.nan),
            (inVar >= uBnd, np.nan),
            (True, inVar),
            ])

        self.stringVariants = {}
        self.inVars = [inVar, lBnd, uBnd]
        self.var = var

        super().__init__(*args, **kwargs)

class Operations(Functions):

    opTag = 'Operation'

    def __init__(self, *args, uwop = None, **kwargs):

        if not uwop in uwNamesToFns:
            raise Exception
        opFn = uwNamesToFns[uwop]

        var = opFn(*args)

        self.stringVariants = {'uwop': uwop}
        self.inVars = [convert(arg) for arg in args]
        self.var = var

        super().__init__(*args, **kwargs)

class Component(Functions):

    opTag = 'Component'

    def __init__(self, inVar, *args, component = 'mag', **kwargs):

        inVar = convert(inVar)

        if not inVar.varDim == inVar.mesh.dim:
            # hence is not a vector and so has no components:
            raise Exception
        if component == 'mag':
            var = fn.math.sqrt(
                fn.math.dot(
                    inVar,
                    inVar
                    )
                )
        else:
            compVec = inVar.meshUtils.comps[component]
            var = fn.math.dot(
                inVar,
                compVec
                )

        self.stringVariants = {'component': component}
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

class Gradient(Functions):

    opTag = 'Gradient'

    def __init__(self, inVar, *args, gradient = 'mag', **kwargs):

        inVar = get_meshVar(
            inVar,
            *args,
            hide = True,
            attach = True,
            **kwargs
            )
        varGrad = inVar.fn_gradient
        if gradient == 'mag':
            var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
        else:
            compVec = inVar.meshUtils.comps[gradient]
            var = fn.math.dot(
                varGrad,
                compVec
                )

        self.stringVariants = {'gradient': gradient}
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

class Comparison(Functions):

    opTag = 'Comparison'

    def __init__(self, inVar0, inVar1, *args, operation = 'equals', **kwargs):

        if not operation in {'equals', 'notequals'}:
            raise Exception

        inVar0, inVar1 = inVars = convert(inVar0, inVar1)
        boolOut = operation == 'equals'
        var = fn.branching.conditional([
            (inVar0 < inVar1 - 1e-18, not boolOut),
            (inVar0 > inVar1 + 1e-18, not boolOut),
            (True, boolOut),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

class Range(Functions):

    opTag = 'Range'

    def __init__(self, inVar0, inVar1, *args, operation = None, **kwargs):

        if not operation in {'in', 'out'}:
            raise Exception

        inVar0, inVar1 = inVars = convert(inVar0), convert(inVar1)
        if operation == 'in':
            inVal = inVar0
            outVal = np.nan
        else:
            inVal = np.nan
            outVal = inVar0
        self._lowerBounds = fn.misc.constant(1.)
        self._upperBounds = fn.misc.constant(1.)
        var = fn.branching.conditional([
            (inVar0 < self._lowerBounds, outVal),
            (inVar0 > self._upperBounds, outVal),
            (True, inVal),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

    def _partial_update(self):
        self._lowerBound.value = self.inVars[1].scales[:,0]
        self._upperBound.value = self.inVars[1].scales[:,1]

class Integral(Functions):

    opTag = 'Integral'

    def __init__(self, inVar, *args, surface = 'volume', **kwargs):

        inVar = get_meshVar(
            inVar,
            *args,
            hide = True,
            attach = True,
            **kwargs
            )

        intMesh = inVar.meshUtils.integrals[surface]
        if surface == 'volume':
            intField = uw.utils.Integral(
                inVar,
                inVar.mesh
                )
        else:
            indexSet = inVar.meshUtils.surfaces[surface]
            intField = uw.utils.Integral(
                inVar,
                inVar.mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )

        var = fn.misc.constant(1.)
        self._intField = intField
        self._intMesh = intMesh

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.var = var
        self.mesh = self.substrate = None

        super().__init__(*args, **kwargs)

    def _partial_update(self):
        self.var.value = \
            self._intField.evaluate()[0] \
            / self._intMesh()

class Quantile(Functions):

    opTag = 'Quantile'

    def __init__(self, inVar, *args, ntiles = 2, nthtile = 0, **kwargs):

        nthtile, ntiles = int(nthtile), int(ntiles)
        if not 0 < nthtile <= ntiles:
            raise Exception

        inVar = convert(inVar)

        self._lowerBound = fn.misc.constant(1.)
        self._upperBound = fn.misc.constant(1.)
        self._ntiles = ntiles
        self._nthtile = nthtile
        l_adj = -1e-18
        if nthtile == ntiles:
            u_adj = -1e-18
        else:
            u_adj = 1e-18
        var = fn.branching.conditional([
            (inVar < self._lowerBound + l_adj, np.nan),
            (inVar > self._upperBound + u_adj, np.nan),
            (True, inVar),
            ])

        self.stringVariants = {
            'nthtile': str(nthtile),
            'ntiles': str(ntiles)
            }
        self.inVars = [inVar]
        self.var = var

        super().__init__(*args, **kwargs)

    def _partial_update(self):
        intervalSize = self.inVar.ranges / self._ntiles
        self._lowerBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self._nthtile - 1)
        self._upperBound.value = self.inVar.scales[:,0] \
            + intervalSize * (self._nthtile)

class Region(Functions):

    opTag = 'Region'

    def __init__(self, inShape, inVar, *args, **kwargs):

        inVar, inShape = inVars = convert(inVar, inShape)

        polygon = inShape.morph(inVar.mesh)
        var = fn.branching.conditional([
            (polygon, inVar),
            (True, np.nan),
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

class Normalise(Functions):

    opTag = 'Normalise'

    def __init__(self, baseVar, normVar, *args, **kwargs):

        baseVar, normVar = inVars = convert(baseVar, normVar)

        inMins = fn.misc.constant(
            [1. for dim in range(baseVar.varDim)]
            )
        inRanges = fn.misc.constant(
            [1. for dim in range(baseVar.varDim)]
            )
        normMins = fn.misc.constant(
            [1. for dim in range(normVar.varDim)]
            )
        normRanges = fn.misc.constant(
            [1. for dim in range(normVar.varDim)]
            )

        var = (baseVar - inMins) / inRanges * normRanges + normMins

        self.inMins = inMins
        self.inRanges = inRanges
        self.normMins = normMins
        self.normRanges = normRanges
        self.baseVar = baseVar
        self.normVar = normVar

        self.stringVariants = {}
        self.inVars = inVars
        self.var = var

        super().__init__(*args, **kwargs)

    def _partial_update(self):

        self.inMins.value = \
            [scale[0] for scale in self.baseVar.scales]
        self.inRanges.value = self.baseVar.ranges
        self.normMins.value = \
            [scale[0] for scale in self.normVar.scales]
        self.normRanges.value = self.normVar.ranges

class GetStat(Functions):

    opTag = 'GetStat'

    def __init__(self, inVar, *args, stat = 'mins', **kwargs):

        if not stat in {'mins', 'maxs', 'ranges'}:
            raise Exception

        inVar = convert(inVar)
        var = fn.misc.constant(
            [1. for dim in range(inVar.varDim)]
            )

        self.stat = stat

        self.stringVariants = {'stat': stat}
        self.inVars = [inVar]
        self.var = var
        self.mesh = self.substrate = None

        super().__init__(*args, **kwargs)

    def _partial_update(self):

        if self.stat == 'mins':
            self.var.value = [scale[0] for scale in self.inVar.scales]
        elif self.stat == 'maxs':
            self.var.value = [scale[1] for scale in self.inVar.scales]
        elif self.stat == 'ranges':
            self.var.value = self.inVar.ranges
        else:
            raise Exception
