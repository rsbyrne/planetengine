import weakref
import numpy as np

from underworld import function as fn
UWFn = fn._function.Function

from .. import utilities
hasher = utilities.hashToInt

# MOST IMPORTS ARE AT THE BOTTOM
# DUE TO CIRCULAR IMPORTS PROBLEM

# _premade_fns = {}

def update_opTag(opTag, stringVariants):
    for key, val in sorted(stringVariants.items()):
        opTag += '_' + str(key) + '=' + str(val)
    return opTag

def get_opHash(varClass, *hashVars, **stringVariants):

    hashList = []

    if varClass is _basetypes.Shape:
        assert len(hashVars) == 1
        vertices = hashVars[0]
        assert type(vertices) == np.ndarray
        hashList.append(vertices)

    elif varClass is _basetypes.Constant:
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

    elif varClass is _basetypes.Variable:
        assert len(hashVars) == 1
        var = UWFn.convert(hashVars[0])
        hashList.append(var.__hash__())

    elif varClass is _basetypes.Parameter:
        assert len(hashVars) == 0
        pass
        # random_hash = random.randint(0, 1e18)
        # hashList.append(random_hash)

    else:

        if varClass is vanilla.Vanilla:
            assert len(hashVars) == 1
            var = UWFn.convert(hashVars[0])
            if not hasattr(var, '_underlyingDataItems'):
                raise Exception
            if not len(var._underlyingDataItems) > 0:
                raise Exception
            inVars = []
            for underlying in sorted(var._underlyingDataItems):
                inVars.append(_convert.convert(underlying))
            hashVars = inVars
            stringVariants = {'UWhash': var.__hash__()}
        else:
            hashVars = _convert.convert(hashVars)

        rootVarHashes = []
        for hashVar in hashVars:
            assert isinstance(hashVar, PlanetVar)
            if len(hashVar.rootVars) == 0:
                rootVarHashes.append(hashVar.__hash__())
            else:
                for rootVar in hashVar.rootVars:
                    rootVarHashes.append(rootVar.__hash__())
        hashList.extend(list(sorted(set(rootVarHashes))))

    fulltag = update_opTag(varClass.opTag, stringVariants)
    hashList.append(fulltag)
    hashVal = hasher(hashList)

    return hashVal

def get_dType(sample_data):
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
    return dType

class PlanetVar(UWFn):

    inVars = []
    opTag = 'None'

    def __init__(self, *args, hide = False, **kwargs):

        # Determing inVars:

        for index, inVar in enumerate(self.inVars):
            if type(inVar) == _basetypes.Parameter:
                self.parameters.append(self.inVars.pop(index))

        if len(self.inVars) == 1:
            self.inVar = self.inVars[0]

        for inVar in self.inVars:
            if not isinstance(inVar, PlanetVar):
                raise Exception(
                    "Type " + str(type(inVar)) + " is not PlanetVar."
                    )

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

        if type(self) in {
                _basetypes.Constant,
                _basetypes.Variable,
                _basetypes.Shape
                }:
            _argument_fns = [self.var]
        else:
            _argument_fns = [*self.inVars]

        self._fncself = self.var._fncself

        super().__init__(_argument_fns)

        # Other necessary business:

        self.lasthash = 0

        self._set_rootVars()

        self._update()

        # if not self.__class__ is _basetypes.Constant:
        #     self._set_weakref(self) # is static

    #     self._safety_checks()
    #
    # def _safety_checks(self):
    #     if hasattr(self, 'varDim'):
    #         assert self.varDim < 99

    def _set_rootVars(self):
        rootVars = set()
        if not isinstance(self, _basetypes.BaseTypes):
            assert len(self.inVars) > 0
            for inVar in self.inVars:
                if isinstance(inVar, _basetypes.BaseTypes):
                    rootVars.add(inVar)
                else:
                    for rootVar in inVar.rootVars:
                        rootVars.add(rootVar)
        assert all(
            [isinstance(rootVar, _basetypes.BaseTypes) \
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
        self._update_summary_stats()

    def _check_hash(self, lazy = False):
        currenthash = 0
        for rootVar in self.rootVars:
            hashVal = rootVar._check_hash(lazy = lazy)
            currenthash += hashVal
        return currenthash

    def _has_changed(self, lazy = False):
        currenthash = self._check_hash(lazy = lazy)
        has_changed = bool(
            mpi.comm.allreduce(
                currenthash - self.lasthash
                )
            )
        self.lasthash = currenthash
        return has_changed

    def _set_summary_stats(self):
        if isinstance(self, _function.Function) \
                or type(self) == _basetypes.Variable:
            if self.varDim == 1:
                minmax = fn.view.min_max(self.var)
            else:
                fn_norm = fn.math.sqrt(
                    fn.math.dot(
                        self,
                        self
                        )
                    )
                minmax = fn.view.min_max(
                    self,
                    fn_norm = fn_norm
                    )
            minFn = minmax.min_global
            maxFn = minmax.max_global
            self._minmax = minmax
            rangeFn = lambda: abs(minFn() - maxFn())
        elif isinstance(self, _reduction.Reduction) \
                or type(self) == _basetypes.Constant:
            minFn = lambda: min(self.value)
            maxFn = lambda: max(self.value)
            rangeFn = lambda: maxFn() - minFn()
        elif type(self) in {
                _basetypes.Parameter,
                _basetypes.Shape
                }:
            minFn = maxFn = rangeFn = lambda: None
        else:
            raise Exception

        self._minFn = minFn
        self._maxFn = maxFn
        self._rangeFn = rangeFn

    def minFn(self):
        if not hasattr(self, '_minFn'):
            self._set_summary_stats()
        return self._minFn()
    def maxFn(self):
        if not hasattr(self, '_maxFn'):
            self._set_summary_stats()
        return self._maxFn()
    def rangeFn(self):
        if not hasattr(self, '_rangeFn'):
            self._set_summary_stats()
        return self._rangeFn()

    def _update_summary_stats(self):
        if (isinstance(self, _function.Function) \
                or type(self) == _basetypes.Variable
                ) \
                and hasattr(self, '_minmax'):
            self._minmax.evaluate(self.substrate)
        if isinstance(self, _reduction.Reduction):
            self.value = self.evaluate(lazy = True)[0]

    def meshVar(self):
        self.update()
        if not any([
                isinstance(self, _function.Function),
                type(self) == _basetypes.Variable
                ]):
            raise Exception
        if self.varType == 'constFn':
            raise Exception
        if not hasattr(self, '_meshVar'):
            projVar = projection.Projection(self)
            # self._meshVar = weakref.ref(projVar)
            # POSSIBLE CIRCULAR REFERENCE!
            self._meshVar = lambda: projVar
        return self._meshVar()
    def gradient(self):
        if not hasattr(self, '_fn_gradient'):
            gradientVar = gradient.Gradient(self)
            # self._fn_gradient = weakref.ref(gradientVar)
            # POSSIBLE CIRCULAR REFERENCE!
            self._fn_gradient = lambda: gradientVar
        return self._fn_gradient()

    # @staticmethod
    # def _set_weakref(self):
    #     weak_reference = weakref.ref(self)
    #     hashKey = self.__hash__()
    #     _premade_fns[hashKey] = weak_reference
    def _input_processing(self, evalInput):
        return evalInput

    def evaluate(self, evalInput = None, lazy = False):
        if not lazy:
            self.update()
        if evalInput is None:
            evalInput = self.substrate
        evalInput = self._input_processing(evalInput)
        return self.var.evaluate(evalInput)

    def __call__(self):
        self.update()
        return self

    def __hash__(self):
        hashVal = get_opHash(
            self.__class__,
            *self._hashVars,
            **self.stringVariants
            )
        return hashVal

    def __add__(self, other):
        return operations.Operations(self, other, uwop = 'add')

    def __sub__(self, other):
        return operations.Operations(self, other, uwop = 'subtract')

    def __mul__(self, other):
        return operations.Operations(self, other, uwop = 'multiply')

    def __truediv__(self, other):
        return operations.Operations(self, other, uwop = 'divide')

    def __gt__(self, other):
        return operations.Operations(self, other, uwop = 'greater')

    def __ge__(self, other):
        return operations.Operations(self, other, uwop = 'greater_equal')

    def __lt__(self, other):
        return operations.Operations(self, other, uwop = 'less')

    def __le__(self, other):
        return operations.Operations(self, other, uwop = 'less_equal')

    def __and__(self, other):
        return operations.Operations(self, other, uwop = 'logical_and')

    def __or__(self, other):
        return operations.Operations(self, other, uwop = 'logical_or')

    def __xor__(self, other):
        return operations.Operations(self, other, uwop = 'logical_xor')

    def __pow__(self, other):
        return operations.Operations(self, other, uwop = 'pow')

    # def __eq__(self, other):
    #     return Comparison(self, other, uwop = 'equals')
    #
    # def __ne__(self, other):
    #     return Comparison(self, other, uwop = 'notequals')

# IMPORTS AT BOTTOM
# DUE TO CIRCULAR IMPORTS PROBLEM
from . import vanilla
from . import _convert
from . import _basetypes
from . import _function
from . import _reduction
from . import projection
from . import gradient
from . import operations
from .. import utilities
from .. import mpi
