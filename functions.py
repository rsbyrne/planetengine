import functools
import itertools
import weakref
import hashlib
import random

import numpy as np
import underworld as uw
from underworld import function as fn
from underworld.function._function import Function as UWFn

from . import utilities

from .utilities import hashToInt as hasher

from .meshutils import get_meshUtils
from .mapping import unbox
from .shapes import interp_shape

_premade_fns = {}

def update_opTag(opTag, stringVariants):
    for key, val in sorted(stringVariants.items()):
        opTag += '_' + str(key) + '=' + str(val)
    return opTag

def get_opHash(varClass, *hashVars, stringVariants = {}):
    hashList = []
    if varClass is Shape:
        assert len(hashVars) == 1
        vertices = hashVars[0]
        assert type(vertices) == np.ndarray
        hashList.append(vertices)
    elif varClass is Constant:
        assert len(hashVars) == 1
        var = UWFn.convert(hashVars[0])
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
        assert len(hashVars) == 1
        var = UWFn.convert(hashVars[0])
        hashList.append(var.__hash__())
    elif varClass is Parameter:
        assert len(hashVars) == 0
        pass
        # random_hash = random.randint(0, 1e18)
        # hashList.append(random_hash)
    else:
        rootVars = set()
        for hashVar in hashVars:
            assert isinstance(hashVar, PlanetVar)
            rootVars = rootVars.union(
                rootVars,
                hashVar.rootVars
                )
        for rootVar in rootVars:
            hashList.append(rootVar.__hash__())
    fulltag = update_opTag(varClass.opTag, stringVariants)
    hashList.append(fulltag)
    hashVal = hasher(hashList)
    return hashVal

# def _construct(
#         *inVars,
#         varClass = None,
#         stringVariants = {},
#         **kwargs
#         ):
#
#     if not varClass in {Constant, Variable, Shape, Parameter}:
#         inVars = [convert(inVar) for inVar in inVars]
#
#     # if varClass is Constant:
#     #     # constants don't get saved!!!
#     #     outObj = varClass(
#     #         *inVars,
#     #         **kwargs
#     #         )
#     # else:
#     opHash = get_opHash(
#         varClass,
#         *inVars,
#         stringVariants = stringVariants
#         )
#     outObj = None
#     if opHash in _premade_fns:
#         print("Returning premade!")
#         outObj = _premade_fns[opHash]() # is weakref
#     if outObj is None:
#         print("Making a new one!")
#         outObj = varClass(
#             *inVars,
#             **stringVariants,
#             **kwargs
#             )
#
#     assert not outObj is None
#     return outObj

def _construct(
        *inVars,
        varClass = None,
        stringVariants = {}
        ):

    outObj = varClass(
        *inVars,
        **stringVariants
        )

    return outObj

def _convert(var, varName = 'anon'):
    if isinstance(var, PlanetVar):
        return var
    # elif hasattr(var, 'planetVar'):
    #     return var.planetVar
    else:
        try:
            var = UWFn.convert(var)
            if var is None:
                raise Exception
            if len(list(var._underlyingDataItems)) == 0:
                # hence is a constant!
                valString = utilities.stringify(
                    var.evaluate()[0]
                    )
                stringVariants = {'val': valString}
                var = _construct(
                    var,
                    varClass = Constant,
                    stringVariants = stringVariants
                    )
            else:
                stringVariants = {'varName': varName}
                var = _construct(
                    var,
                    varClass = Variable,
                    stringVariants = stringVariants
                    )
        except:
            try:
                stringVariants = {'varName': varName}
                var = _construct(
                    var,
                    varClass = Shape,
                    stringVariants = stringVariants
                    )
            except:
                raise Exception
        return var

def convert(*args, return_tuple = False):
    if len(args) == 1:
        arg = args[0]
        # if type(arg) == tuple:
        #     converted = _tuple_convert(arg)
        # elif type(arg) == list:
        #     converted = _multi_convert(*arg)
        if type(arg) == dict:
            converted = _dict_convert(arg)
        else:
            converted = _convert(arg)
    elif len(args) == 2:
        if type(args[0]) == str:
            converted = _convert(args[1], args[0])
        elif type(args[1]) == str:
            converted = _convert(args[0], args[1])
        else:
            converted = _multi_convert(*args)
    else:
        converted = _multi_convert(*args)
    if type(converted) == tuple:
        return converted
    else:
        if return_tuple:
            return (converted,)
        else:
            return converted

get_planetVar = convert

def _multi_convert(*args):
    all_converted = []
    for arg in args:
        all_converted.append(convert(arg))
    return tuple(all_converted)

def _tuple_convert(inTuple):
    var, varName = inTuple
    return _convert(var, varName)

def _dict_convert(inDict):
    all_converted = {}
    for varName, var in sorted(inDict.items()):
        newVar = _convert(var, varName)
        all_converted[varName] = newVar
    return all_converted

def get_projection(
        inVar,
        *args,
        hide = False,
        attach = False,
        **kwargs
        ):
    inVar = convert(inVar)
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
    inVar = convert(inVar, **kwargs)
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

        # self.inVars = list(self.inVars)
        for index, inVar in enumerate(self.inVars):
            if type(inVar) == Parameter:
                self.parameters.append(self.inVars.pop(index))

        if len(self.inVars) == 1:
            self.inVar = self.inVars[0]

        if not hasattr(self, '_hashVars'):
            assert not isinstance(self, BaseTypes)
            self._hashVars = self.inVars

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

        self._update()

        if not self.__class__ is Constant:
            self._set_weakref(self) # is static

    def _set_rootVars(self):
        rootVars = set()
        if not isinstance(self, BaseTypes):
            assert len(self.inVars) > 0
            for inVar in self.inVars:
                if isinstance(inVar, BaseTypes):
                    rootVars.add(inVar)
                else:
                    for rootVar in inVar.rootVars:
                        rootVars.add(rootVar)
        assert all(
            [isinstance(rootVar, BaseTypes) \
            for rootVar in list(rootVars)]
            )
        self.rootVars = rootVars

    def _partial_update(self):
        pass

    def update(self, lazy = False):
        has_changed = self._has_changed(lazy = lazy)
        if has_changed:
            self._update()

    def _update(self):
        for inVar in self.inVars:
            inVar.update(lazy = True)
        for parameter in self.parameters:
            parameter.update()
        self._partial_update()
        # self.data = self.evaluate(lazy = True)
        # self._set_summary_stats()
        if hasattr(self, 'data'):
            self._get_data(setAsAtt = True)
        if hasattr(self, 'scales'):
            self._get_scales(setAsAtt = True, refresh = True)
        if hasattr(self, 'ranges'):
            self._get_ranges(setAsAtt = True, refresh = True)

    def _check_hash(self, lazy = False):
        currenthash = 0
        for rootVar in self.rootVars:
            hashVal = rootVar._check_hash(lazy = lazy)
            currenthash += hashVal
        return currenthash

    def _has_changed(self, lazy = False):
        currenthash = self._check_hash(lazy = lazy)
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

    def _get_data(self, setAsAtt = False, refresh = False):
        if hasattr(self, 'data') and not refresh:
            data = self.data
        else:
            data = self.evaluate(
                lazy = True
                )
        if setAsAtt:
            self.data = data
        return data

    def _get_scales(self, setAsAtt = False, refresh = False):
        if hasattr(self, 'scales') and not refresh:
            scales = self.scales
        else:
            data = self._get_data(setAsAtt = setAsAtt)
            scales = utilities.get_scales(data)
        if setAsAtt:
            self.scales = scales
        return scales

    def _get_ranges(self, setAsAtt = False, refresh = False):
        if hasattr(self, 'ranges') and not refresh:
            ranges = self.ranges
        else:
            scales = self._get_scales(setAsAtt = setAsAtt)
            ranges = np.array(
                [maxVal - minVal for minVal, maxVal in scales]
                )
        if setAsAtt:
            self.ranges = ranges
        return ranges

    @staticmethod
    def _set_weakref(self):
        weak_reference = weakref.ref(self)
        hashKey = self.__hash__()
        _premade_fns[hashKey] = weak_reference

    def evaluate(self, evalInput = None, lazy = False):
        if not lazy:
            self.update()
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def __call__(self):
        self.update()
        return self

    def __hash__(self):
        hashVal = get_opHash(
            self.__class__,
            *self._hashVars,
            stringVariants = self.stringVariants
            )
        return hashVal

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
        super().__init__(**kwargs)

    def evaluate(self, evalInput = None, **kwargs):
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def _update(self, **kwargs):
        self._partial_update()
        # self._set_summary_stats()

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
        self._currenthash = hasher(self.value)
        self._hashVars = [var]
        self.data = np.array([[val,] for val in self.value])

        self.stringVariants = {'val': valString}
        self.inVars = []
        self.parameters = []
        self.var = var
        self.mesh = self.substrate = None

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return self._currenthash

class Parameter(BaseTypes):

    opTag = 'Parameter'

    def __init__(self, inFn, *args, varLen = 1, dType = 'double', **kwargs):

        defaults = {
            'int': 1,
            'double': 1.,
            'boolean': True,
            }
        if not dType in defaults:
            raise Exception
        if not varLen > 0:
            raise Exception
        initialVal = [
            defaults[dType] for i in range(varLen)
            ]
        var = fn.misc.constant(initialVal)
        if not len(list(var._underlyingDataItems)) == 0:
            raise Exception

        self._hashVars = []
        self.stringVariants = {}
        self.inVars = []
        self.parameters = []
        self.var = var
        self.mesh = self.substrate = None

        self._paramfunc = inFn
        self._hashval = random.randint(1, 1e18)

        self._update_attributes()

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return random.randint(0, 1e18)

    def _update_attributes(self):
        self.value = self.var.evaluate()[0]
        self.data = np.array([[val,] for val in self.value])

    def _partial_update(self):
        self.var.value = self._paramfunc()
        self._update_attributes()

    def __hash__(self):
        return self._hashval

class Variable(BaseTypes):

    opTag = 'Variable'

    def __init__(self, inVar, varName = 'anon', *args, **kwargs):

        var = UWFn.convert(inVar)
        if var is None:
            raise Exception

        self._hashVars = [var]

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = var
        if type(var) == fn.misc.constant:
            if not len(list(var._underlyingDataItems)) == 0:
                raise Exception
            self.mesh = self.substrate = None
            self.value = var.evaluate()[0]
        else:
            if len(list(var._underlyingDataItems)) == 0:
                raise Exception
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

        super().__init__(**kwargs)

    def _check_hash(self, lazy = False):
        if lazy and hasattr(self, '_currenthash'):
            return self._currenthash
        else:
            self._update() # resets self.data
            currenthash = hasher(self.data)
            self._currenthash = currenthash
        return currenthash

    def _partial_update(self):
        if hasattr(self.var, 'data'):
            self.data = self.var.data
        elif hasattr(self.var, 'value'):
            self.data = np.array([[val,] for val in self.value])
        else:
            # i.e. is a function
            self.data = self.var.evaluate(self.substrate)
        if hasattr(self, 'scales'):
            self._get_scales(setAsAtt = True, refresh = True)
        if hasattr(self, 'ranges'):
            self._get_ranges(setAsAtt = True, refresh = True)

class Shape(BaseTypes):

    opTag = 'Shape'

    def __init__(self, vertices, varName = 'anon', *args, **kwargs):

        shape = fn.shape.Polygon(vertices)
        self.vertices = vertices
        self.richvertices = interp_shape(self.vertices)
        self.morphs = {}
        self._currenthash = hasher(self.vertices)

        self._hashVars = [self.vertices,]
        self.data = self.vertices

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = shape
        self.mesh = self.substrate = None

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return self._currenthash

    def morph(self, mesh):
        try:
            morphpoly = self.morphs[mesh]
        except:
            morphverts = unbox(mesh, self.richvertices)
            morphpoly = fn.shape.Polygon(morphverts)
            self.morphs[mesh] = morphpoly
        return morphpoly

class Function(PlanetVar):

    def __init__(self, *args, **kwargs):

        super().__init__(**kwargs)

class Projection(Function):

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
        self.parameters = []
        self.var = var

        self.fn_gradient = var.fn_gradient

        super().__init__(**kwargs)

    def _partial_update(self):
        self._projector.solve()
        if self.inVar.dType in ('int', 'boolean'):
            rounding = 1
        else:
            rounding = 6
        self.var.data[:] = np.round(
            self.var.data,
            rounding
            )

class Substitute(Function):

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
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Binarise(Function):

    opTag = 'Binarise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        if inVar.dType == 'double':
            var = 0. * inVar + fn.branching.conditional([
                (fn.math.abs(inVar) > 1e-18, 1.),
                (True, 0.),
                ])
        elif inVar.dType == 'boolean':
            var = 0. * inVar + fn.branching.conditional([
                (inVar, 1.),
                (True, 0.),
                ])
        elif inVar.dType == 'int':
            var = 0 * inVar + fn.branching.conditional([
                (inVar, 1),
                (True, 0),
                ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Booleanise(Function):

    opTag = 'Booleanise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        var = fn.branching.conditional([
            (fn.math.abs(inVar) < 1e-18, False),
            (True, True),
            ])

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class HandleNaN(Function):

    opTag = 'HandleNaN'

    def __init__(self, inVar, handleVal, *args, **kwargs):

        inVar, handleVal = inVars = convert(inVar, handleVal)

        var = fn.branching.conditional([
            (inVar < np.inf, inVar),
            (True, handleVal),
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def zero(*args, **kwargs):
        return HandleNaN(*args, handleVal = 0., **kwargs)

    @staticmethod
    def one(*args, **kwargs):
        return HandleNaN(*args, handleVal = 1., **kwargs)

class Clip(Function):

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
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Interval(Function):

    opTag = 'Interval'

    def __init__(self, inVar, lBnd, uBnd, *args, **kwargs):

        inVar, lBnd, uBnd = inVars = convert(inVar, lBnd, uBnd)

        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (inVar <= lBnd, nullVal),
            (inVar >= uBnd, nullVal),
            (True, inVar),
            ])

        self.stringVariants = {}
        self.inVars = [inVar, lBnd, uBnd]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Operations(Function):

    opTag = 'Operation'

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

    def __init__(self, *args, uwop = None, **kwargs):

        if not uwop in self.uwNamesToFns:
            raise Exception
        opFn = self.uwNamesToFns[uwop]

        var = opFn(*args)

        self.stringVariants = {'uwop': uwop}
        self.inVars = [convert(arg) for arg in args]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def pow(*args, **kwargs):
        return Operations(*args, uwop = 'pow', **kwargs)

    @staticmethod
    def abs(*args, **kwargs):
        return Operations(*args, uwop = 'abs', **kwargs)

    @staticmethod
    def cosh(*args, **kwargs):
        return Operations(*args, uwop = 'cosh', **kwargs)

    @staticmethod
    def acosh(*args, **kwargs):
        return Operations(*args, uwop = 'acosh', **kwargs)

    @staticmethod
    def tan(*args, **kwargs):
        return Operations(*args, uwop = 'tan', **kwargs)

    @staticmethod
    def asin(*args, **kwargs):
        return Operations(*args, uwop = 'asin', **kwargs)

    @staticmethod
    def log(*args, **kwargs):
        return Operations(*args, uwop = 'log', **kwargs)

    @staticmethod
    def atanh(*args, **kwargs):
        return Operations(*args, uwop = 'atanh', **kwargs)

    @staticmethod
    def sqrt(*args, **kwargs):
        return Operations(*args, uwop = 'sqrt', **kwargs)

    @staticmethod
    def abs(*args, **kwargs):
        return Operations(*args, uwop = 'abs', **kwargs)

    @staticmethod
    def log10(*args, **kwargs):
        return Operations(*args, uwop = 'log10', **kwargs)

    @staticmethod
    def sin(*args, **kwargs):
        return Operations(*args, uwop = 'sin', **kwargs)

    @staticmethod
    def asinh(*args, **kwargs):
        return Operations(*args, uwop = 'asinh', **kwargs)

    @staticmethod
    def log2(*args, **kwargs):
        return Operations(*args, uwop = 'log2', **kwargs)

    @staticmethod
    def atan(*args, **kwargs):
        return Operations(*args, uwop = 'atan', **kwargs)

    @staticmethod
    def sinh(*args, **kwargs):
        return Operations(*args, uwop = 'sinh', **kwargs)

    @staticmethod
    def cos(*args, **kwargs):
        return Operations(*args, uwop = 'cos', **kwargs)

    @staticmethod
    def tanh(*args, **kwargs):
        return Operations(*args, uwop = 'tanh', **kwargs)

    @staticmethod
    def erf(*args, **kwargs):
        return Operations(*args, uwop = 'erf', **kwargs)

    @staticmethod
    def erfc(*args, **kwargs):
        return Operations(*args, uwop = 'erfc', **kwargs)

    @staticmethod
    def exp(*args, **kwargs):
        return Operations(*args, uwop = 'exp', **kwargs)

    @staticmethod
    def acos(*args, **kwargs):
        return Operations(*args, uwop = 'acos', **kwargs)

    @staticmethod
    def dot(*args, **kwargs):
        return Operations(*args, uwop = 'dot', **kwargs)

    @staticmethod
    def add(*args, **kwargs):
        return Operations(*args, uwop = 'add', **kwargs)

    @staticmethod
    def subtract(*args, **kwargs):
        return Operations(*args, uwop = 'subtract', **kwargs)

    @staticmethod
    def multiply(*args, **kwargs):
        return Operations(*args, uwop = 'multiply', **kwargs)

    @staticmethod
    def divide(*args, **kwargs):
        return Operations(*args, uwop = 'divide', **kwargs)

    @staticmethod
    def greater(*args, **kwargs):
        return Operations(*args, uwop = 'greater', **kwargs)

    @staticmethod
    def greater_equal(*args, **kwargs):
        return Operations(*args, uwop = 'greater_equal', **kwargs)

    @staticmethod
    def less(*args, **kwargs):
        return Operations(*args, uwop = 'less', **kwargs)

    @staticmethod
    def less_equal(*args, **kwargs):
        return Operations(*args, uwop = 'less_equal', **kwargs)

    @staticmethod
    def logical_and(*args, **kwargs):
        return Operations(*args, uwop = 'logical_and', **kwargs)

    @staticmethod
    def logical_or(*args, **kwargs):
        return Operations(*args, uwop = 'logical_or', **kwargs)

    @staticmethod
    def logical_xor(*args, **kwargs):
        return Operations(*args, uwop = 'logical_xor', **kwargs)

    @staticmethod
    def input(*args, **kwargs):
        return Operations(*args, uwop = 'input', **kwargs)

class Component(Function):

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
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def mag(*args, **kwargs):
        return Component(*args, component = 'mag', **kwargs)

    def x(*args, **kwargs):
        return Component(*args, component = 'x', **kwargs)

    def y(*args, **kwargs):
        return Component(*args, component = 'y', **kwargs)

    def z(*args, **kwargs):
        return Component(*args, component = 'z', **kwargs)

    @staticmethod
    def rad(*args, **kwargs):
        return Component(*args, component = 'rad', **kwargs)

    @staticmethod
    def ang(*args, **kwargs):
        return Component(*args, component = 'ang', **kwargs)

    @staticmethod
    def coang(*args, **kwargs):
        return Component(*args, component = 'coang', **kwargs)

class Merge(Function):

    opTag = 'Merge'

    def __init__(self, *args, **kwargs):

        inVars = convert(*args)

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
        self.inVars = inVars
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        for index, inVar in enumerate(self.inVars):
            self.var.data[:, index] = inVar._get_data(True)[:, 0]

    @staticmethod
    def annulise(inVar):
        inVar = convert(inVar)
        comps = []
        comps.append(Component(inVar, component = 'ang'))
        comps.append(Component(inVar, component = 'rad'))
        if inVar.mesh.dim == 3:
            comps.append(Component(inVar, component = 'coang'))
        var = Merge(*comps)
        return var

    @staticmethod
    def cartesianise(inVar):
        inVar = convert(inVar)
        comps = []
        comps.append(Component(inVar, component = 'x'))
        comps.append(Component(inVar, component = 'y'))
        if inVar.mesh.dim == 3:
            comps.append(Component(inVar, component = 'z'))
        var = Merge(*comps)
        return var

class Split(Function):

    opTag = 'Split'

    def __init__(self, inVar, *args, column = 0, **kwargs):

        inVar = convert(inVar)

        if not inVar.varDim > 1:
            raise Exception
        if inVar.substrate is None:
            raise Exception

        if inVar.meshbased:
            var = inVar.substrate.add_variable(
                1,
                inVar.dType
                )
        else:
            var = inVar.substrate.add_variable(
                inVar.dType,
                1
                )

        self.column = column

        self.stringVariants = {'column': str(column)}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self.var.data[:, 0] = self.inVar._get_data(True)[:, self.column]

    @staticmethod
    def getall(inVar):
        inVar = convert(inVar)
        returnVars = []
        for dim in range(inVar.varDim):
            returnVars.append(Split(inVar, column = dim))
        return tuple(returnVars)

class Gradient(Function):

    opTag = 'Gradient'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        inVar = get_meshVar(
            inVar,
            *args,
            hide = False,
            attach = True,
            **kwargs
            )
        var = inVar.fn_gradient

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def mag(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'mag', **kwargs)

    @staticmethod
    def rad(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'rad', **kwargs)

    @staticmethod
    def ang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'ang', **kwargs)

    @staticmethod
    def coang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'coang', **kwargs)

class Comparison(Function):

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
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def isequal(*args, **kwargs):
        return Comparison(*args, operation = 'equals', **kwargs)

    @staticmethod
    def isnotequal(*args, **kwargs):
        return Comparison(*args, operation = 'notequals', **kwargs)

class Range(Function):

    opTag = 'Range'

    def __init__(self, inVar0, inVar1, *args, operation = None, **kwargs):

        if not operation in {'in', 'out'}:
            raise Exception

        inVar0, inVar1 = inVars = convert(inVar0), convert(inVar1)
        nullVal = [np.nan for dim in range(inVar0.varDim)]
        if operation == 'in':
            inVal = inVar0
            outVal = nullVal
        else:
            inVal = nullVal
            outVal = inVar0
        lowerBounds = Parameter(
            lambda: inVars[1]._get_scales(True)[:,0],
            len = 1,
            dType = 'double'
            )
        upperBounds = Parameter(
            lambda: inVars[1]._get_scales(True)[:,1],
            len = 1,
            dType = 'double'
            )
        var = fn.branching.conditional([
            (inVar0 < lowerBounds, outVal),
            (inVar0 > upperBounds, outVal),
            (True, inVal),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = inVars
        self.parameters = [lowerBounds, upperBounds]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def inrange(*args, **kwargs):
        return Range(*args, operation = 'in', **kwargs)

    @staticmethod
    def outrange(*args, **kwargs):
        return Range(*args, operation = 'out', **kwargs)

class Filter(Function):

    opTag = 'Filter'

    def __init__(self, inVar, filterVal, outVar, *args, **kwargs):

        inVar, filterVal, outVar = inVars = convert(
            inVar, filterVal, outVar
            )

        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (fn.math.abs(inVar - filterVal) < 1e-18, outVar),
            (True, nullVal)
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Quantiles(Function):

    opTag = 'Quantiles'

    def __init__(self, inVar, *args, ntiles = 5, **kwargs):

        inVar = convert(inVar)

        # if not inVar.varDim == 1:
        #     raise Exception

        interval = Parameter(
            lambda: inVar._get_ranges(True) / ntiles,
            inVar.varDim,
            'double'
            )
        minVal = Parameter(
            lambda: inVar._get_scales(True)[:,0],
            inVar.varDim,
            'double'
            )

        clauses = []
        for ntile in range(1, ntiles):
            clause = (
                inVar <= minVal + interval * float(ntile),
                float(ntile)
                )
            clauses.append(clause)
        clauses.append(
            (True, float(ntiles))
            )
        rawvar = fn.branching.conditional(clauses)
        var = fn.branching.conditional([
            (inVar < np.inf, rawvar),
            (True, np.nan)
            ])

        self.stringVariants = {
            'ntiles': str(ntiles)
            }
        self.inVars = [inVar]
        self.parameters = [interval, minVal]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def median(*args, **kwargs):
        return Quantiles(*args, ntiles = 2, **kwargs)

    @staticmethod
    def terciles(*args, **kwargs):
        return Quantiles(*args, ntiles = 3, **kwargs)

    @staticmethod
    def quartiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 4, **kwargs)

    @staticmethod
    def quintiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 5, **kwargs)

    @staticmethod
    def deciles(*args, **kwargs):
        return Quantiles(*args, ntiles = 10, **kwargs)

    @staticmethod
    def percentiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 100, **kwargs)

class Quantile(Function):

    opTag = 'Quantile'

    def __init__(self, inVar, *args, ntiles = 2, nthtile = 0, **kwargs):

        nthtile, ntiles = int(nthtile), int(ntiles)
        if not 0 < nthtile <= ntiles:
            raise Exception

        inVar = convert(inVar)

        minVal = Parameter(lambda: inVar._get_scales(True)[:,0])
        intervalSize = Parameter(lambda: inVar._get_ranges(True) / ntiles)
        lowerBound = Parameter(lambda: minVal + intervalSize * (nthtile - 1))
        upperBound = Parameter(lambda: minVal + intervalSize * nthtile)

        l_adj = -1e-18
        if nthtile == ntiles:
            u_adj = -1e-18
        else:
            u_adj = 1e-18

        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (inVar < lowerBound + l_adj, nullVal),
            (inVar > upperBound + u_adj, nullVal),
            (True, inVar),
            ])

        self.stringVariants = {
            'nthtile': str(nthtile),
            'ntiles': str(ntiles)
            }
        self.inVars = [inVar]
        self.parameters = [minVal, intervalSize, lowerBound, upperBound]
        self.var = var

        super().__init__(**kwargs)

class Region(Function):

    opTag = 'Region'

    def __init__(self, inVar, inShape, *args, **kwargs):

        inVar, inShape = inVars = convert(inVar, inShape)

        polygon = inShape.morph(inVar.mesh)
        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (polygon, inVar),
            (True, nullVal),
            ])

        self.stringVariants = {}
        self.inVars = inVars
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Surface(Function):

    opTag = 'Surface'

    def __init__(self, inVar, *args, surface = 'inner', **kwargs):

        inVar = convert(inVar)

        if inVar.substrate is None:
            raise Exception

        self._surface = \
            inVar.mesh.meshUtils.surfaces[surface]

        if not inVar.meshbased:
            inVar = get_meshVar(inVar)

        var = inVar.mesh.add_variable(
            inVar.varDim,
            inVar.dType
            )
        var.data[:] = \
            [np.nan for dim in range(inVar.varDim)]

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self.var.data[self._surface] = \
            np.round(
                self.inVars[0].evaluate(
                    self.inVars[0].mesh.data[self._surface]
                    ),
                6
                )

class Normalise(Function):

    opTag = 'Normalise'

    def __init__(self, baseVar, normVar, *args, **kwargs):

        baseVar, normVar = inVars = convert(baseVar, normVar)

        inMins = Parameter(
            lambda: [float(scale[0]) for scale in baseVar._get_scales(True)],
            baseVar.varDim
            )
        inRanges = Parameter(
            lambda: [float(val) for val in baseVar._get_ranges(True)],
            baseVar.varDim
            )
        normMins = Parameter(
            lambda: [float(scale[0]) for scale in normVar._get_scales(True)],
            normVar.varDim
            )
        normRanges = Parameter(
            lambda: [float(val) for val in normVar._get_ranges(True)],
            normVar.varDim
            )

        var = (baseVar - inMins) / inRanges * normRanges + normMins

        self.stringVariants = {}
        self.inVars = inVars
        self.parameters = [inMins, inRanges, normMins, normRanges]
        self.var = var

        super().__init__(**kwargs)

class Reduction(PlanetVar):

    def __init__(self, *args, **kwargs):

        self.mesh = self.substrate = None

        super().__init__(**kwargs)

class GetStat(Reduction):

    opTag = 'GetStat'

    def __init__(self, inVar, *args, stat = 'mins', **kwargs):

        if not stat in {'mins', 'maxs', 'ranges'}:
            raise Exception

        inVar = convert(inVar)

        if stat == 'mins':
            var = Parameter(
                lambda: [scale[0] for scale in inVar._get_scales(True)],
                inVar.varDim
                )
        elif stat == 'maxs':
            var = Parameter(
                lambda: [scale[1] for scale in inVar._get_scales(True)],
                inVar.varDim
                )
        elif stat == 'ranges':
            var = Parameter(
                lambda: inVar._get_ranges(True),
                inVar.varDim
                )

        self.stringVariants = {'stat': stat}
        self.inVars = [inVar]
        self.parameters = [var]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def mins(*args, **kwargs):
        return GetStat(*args, stat = 'mins', **kwargs)

    @staticmethod
    def maxs(*args, **kwargs):
        return GetStat(*args, stat = 'maxs', **kwargs)

    @staticmethod
    def ranges(*args, **kwargs):
        return GetStat(*args, stat = 'ranges', **kwargs)

class Integral(Reduction):

    opTag = 'Integral'

    def __init__(self, inVar, *args, surface = 'volume', **kwargs):

        # inVar = get_meshVar(
        #     inVar,
        #     *args,
        #     hide = True,
        #     attach = True,
        #     **kwargs
        #     )

        inVar = convert(inVar)

        if isinstance(inVar, Reduction):
            raise Exception

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

        def int_eval():
            val = intField.evaluate()[0]
            val /= intMesh()
            return val
        var = Parameter(int_eval)

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.parameters = [var]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def volume(*args, **kwargs):
        return Integral(*args, surface = 'volume', **kwargs)

    @staticmethod
    def inner(*args, **kwargs):
        return Integral(*args, surface = 'inner', **kwargs)

    @staticmethod
    def outer(*args, **kwargs):
        return Integral(*args, surface = 'outer', **kwargs)

    @staticmethod
    def left(*args, **kwargs):
        return Integral(*args, surface = 'left', **kwargs)

    @staticmethod
    def right(*args, **kwargs):
        return Integral(*args, surface = 'right', **kwargs)

    @staticmethod
    def front(*args, **kwargs):
        return Integral(*args, surface = 'front', **kwargs)

    @staticmethod
    def back(*args, **kwargs):
        return Integral(*args, surface = 'back', **kwargs)
