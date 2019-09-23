class Function(PlanetVar):

    def __init__(self, *args, **kwargs):

        for inVar in self.inVars:
            if not isinstance(inVar, PlanetVar):
                raise Exception(
                    "Type " + str(type(inVar)) + " is not PlanetVar."
                    )

        self._detect_substrates()
        self._detect_attributes()
        if not self.varType == 'constFn':
            self._detect_scales_bounds()
        self._hashVars = self.inVars

        super().__init__(**kwargs)

    def _detect_substrates(self):
        meshes = set()
        substrates = set()
        for inVar in self.inVars:
            if hasattr(inVar, 'mesh'):
                if not inVar.mesh is None:
                    meshes.add(inVar.mesh)
            if hasattr(inVar, 'substrate'):
                if not inVar.substrate is None:
                    substrates.add(inVar.substrate)
        if len(meshes) == 1:
            self.mesh = list(meshes)[0]
            self.meshUtils = get_meshUtils(self.mesh)
        elif len(meshes) == 0:
            self.mesh = None
        else:
            raise Exception
        if len(substrates) == 1:
            self.substrate = list(substrates)[0]
        elif len(substrates) == 0:
            self.substrate = None
        else:
            raise Exception

    def _detect_attributes(self):
        if not self.mesh is None and self.substrate is self.mesh:
            self.meshbased = True
            self.varType = 'meshFn'
            sample_data = self.var.evaluate(self.mesh.data[0:1])
        else:
            self.meshbased = False
            if self.substrate is None:
                self.varType = 'constFn'
                sample_data = self.var.evaluate()
            else:
                self.varType = 'swarmFn'
                sample_data = self.var.evaluate(self.substrate.data[0:1])
        self.dType = get_dType(sample_data)
        self.varDim = sample_data.shape[1]

    def _detect_scales_bounds(self):
        fields = []
        for inVar in self.inVars:
            if type(inVar) == Variable:
                fields.append(inVar)
            elif isinstance(inVar, Function):
                fields.append(inVar)
        inscales = []
        inbounds = []
        for inVar in fields:
            if hasattr(inVar, 'scales'):
                if inVar.varDim == self.varDim:
                    inscales.append(inVar.scales)
                else:
                    inscales.append(inVar.scales * self.varDim)
            else:
                inscales.append(
                    [['.', '.']] * self.varDim
                    ) # i.e. perfectly free
            if hasattr(inVar, 'bounds'):
                if inVar.varDim == self.varDim:
                    inbounds.append(inVar.bounds)
                else:
                    inbounds.append(inVar.bounds * self.varDim)
            else:
                inbounds.append(
                    [['.'] * self.mesh.dim ** 2] * self.varDim
                    ) # i.e. perfectly free
        scales = []
        for varDim in range(self.varDim):
            fixed = not any([
                inscale[varDim] == ['.', '.'] \
                    for inscale in inscales
                ])
            if fixed:
                scales.append('!')
            else:
                scales.append('.')
        bounds = []
        for varDim in range(self.varDim):
            dimBounds = []
            for index in range(self.mesh.dim ** 2):
                fixed = not any([
                    inbound[varDim][index] == '.' \
                        for inbound in inbounds
                    ])
                if fixed:
                    dimBounds.append('!')
                else:
                    dimBounds.append('.')
            bounds.append(dimBounds)
        if not hasattr(self, 'scales'):
            self.scales = scales
        if not hasattr(self, 'bounds'):
            self.bounds = bounds

class Vanilla(Function):

    opTag = 'Vanilla'

    def __init__(self, inVar, *args, **kwargs):

        var = UWFn.convert(inVar)

        if not hasattr(var, '_underlyingDataItems'):
            raise Exception
        if not len(var._underlyingDataItems) > 0:
            raise Exception

        inVars = convert(tuple(sorted(var._underlyingDataItems)))

        self.stringVariants = {'UWhash': var.__hash__()}
        self.inVars = inVars
        self.parameters = []
        self.var = var

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

        super().__init__(**kwargs)

    def _partial_update(self):
        self._projector.solve()
        allwalls = self.meshUtils.surfaces['all']
        self.var.data[allwalls.data] = \
            self.inVar.evaluate(allwalls)
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
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Binarise(Function):

    opTag = 'Binarise'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        if not inVar.varDim == 1:
            raise Exception

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

        if not inVar.varDim == 1:
            raise Exception

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

        compareVal = [
            np.inf for dim in range(inVar.varDim)
            ]
        var = fn.branching.conditional([
            (inVar < compareVal, inVar),
            (True, handleVal),
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def _NaNFloat(inVar, handleFloat, **kwargs):
        inVar = convert(inVar)
        handleVal = [
            handleFloat for dim in range(inVar.varDim)
            ]
        return HandleNaN(inVar, handleVal = handleVal, **kwargs)

    @staticmethod
    def zeroes(inVar, **kwargs):
        return HandleNaN._NaNFloat(inVar, 0., **kwargs)

    @staticmethod
    def units(inVar, **kwargs):
        return HandleNaN._NaNFloat(inVar, 1., **kwargs)

    @staticmethod
    def mins(inVar, **kwargs):
        handleVal = GetStat.mins(inVar)
        return HandleNaN._NaNFloat(inVar, handleVal, **kwargs)

    @staticmethod
    def maxs(inVar, **kwargs):
        handleVal = GetStat.maxs(inVar)
        return HandleNaN._NaNFloat(inVar, handleVal, **kwargs)

class Clip(Function):

    opTag = 'Clip'

    def __init__(
            self,
            inVar,
            lBnd = None,
            lClipVal = 'null',
            uBnd = None,
            uClipVal = 'null',
            **kwargs
            ):

        inVar = convert(inVar)
        inVars = [inVar]
        stringVariants = {}
        parameters = []
        clauses = []
        nullVal = [np.nan for dim in range(inVar.varDim)]

        if lBnd is None:
            stringVariants['lower'] = 'open'
        else:
            lBnd = convert(lBnd)
            if not lBnd in inVars:
                inVars.append(lBnd)
            lBnd = Parameter(lBnd.minFn)
            parameters.append(lBnd)
            if lClipVal is 'null':
                lClipVal = nullVal
                stringVariants['lower'] = 'null'
            elif lClipVal == 'fill':
                lClipVal = lBnd
                stringVariants['lower'] = 'fill'
            else:
                raise Exception
            clauses.append((inVar < lBnd, lClipVal))

        if uBnd is None:
            stringVariants['lower'] = 'open'
        else:
            uBnd = convert(uBnd)
            if not uBnd in inVars:
                inVars.append(uBnd)
            uBnd = Parameter(uBnd.maxFn)
            parameters.append(uBnd)
            if uClipVal is 'null':
                uClipVal = nullVal
                stringVariants['upper'] = 'null'
            elif uClipVal == 'fill':
                uClipVal = uBnd
                stringVariants['upper'] = 'fill'
            else:
                raise Exception
            clauses.append((inVar > uBnd, uClipVal))

        clauses.append((True, inVar))

        if stringVariants['lower'] == stringVariants['upper']:
            stringVariants['both'] = stringVariants['lower']
            del stringVariants['lower']
            del stringVariants['upper']

        var = fn.branching.conditional(clauses)

        self.stringVariants = stringVariants
        self.inVars = list(inVars)
        self.parameters = parameters
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def torange(inVar, clipVar, **kwargs):
        inVar, clipVar = convert(inVar, clipVar)
        return Clip(
            inVar,
            lBnd = clipVar,
            uBnd = clipVar,
            **kwargs
            )

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

        inVars = convert(args)

        self.stringVariants = {'uwop': uwop}
        self.inVars = list(inVars)
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

        inVars = convert(args)

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
        self.var.data[:, 0] = \
            self.inVar.evaluate()[:, self.column]

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
        inVar = inVar.meshVar()
        # DEBUGGING
        assert not inVar is None

        var = inVar.var.fn_gradient

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        self.scales = [['.', '.']] * inVar.mesh.dim ** 2
        self.bounds = [['.'] * inVar.mesh.dim ** 2] * inVar.varDim

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
        self.inVars = list(inVars)
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
        lowerBounds = Parameter(inVars[1].minFn)
        upperBounds = Parameter(inVars[1].maxFn)
        var = fn.branching.conditional([
            (inVar0 < lowerBounds, outVal),
            (inVar0 > upperBounds, outVal),
            (True, inVal),
            ])

        self.stringVariants = {'operation': operation}
        self.inVars = list(inVars)
        self.parameters = [lowerBounds, upperBounds]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def inrange(*args, **kwargs):
        return Range(*args, operation = 'in', **kwargs)

    @staticmethod
    def outrange(*args, **kwargs):
        return Range(*args, operation = 'out', **kwargs)

class Select(Function):

    opTag = 'Select'

    def __init__(self, inVar, selectVal, outVar = None, **kwargs):

        inVar, selectVal = inVars = convert(
            inVar, selectVal
            )

        if outVar is None:
            outVar = inVar
        else:
            outVar = convert(outVar)
            inVars = tuple([*list(inVars), outVar])
        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (fn.math.abs(inVar - selectVal) < 1e-18, outVar),
            (True, nullVal)
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Filter(Function):

    opTag = 'Filter'

    def __init__(self, inVar, filterVal, outVar = None, **kwargs):

        inVar, filterVal = inVars = convert(
            inVar, filterVal
            )

        if outVar is None:
            outVar = inVar
        else:
            outVar = convert(outVar)
            inVars.append(outVar)
        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (fn.math.abs(inVar - filterVal) < 1e-18, nullVal),
            (True, outVar)
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
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
            lambda: inVar.rangeFn() / ntiles
            )
        minVal = Parameter(
            inVar.minFn
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

        minVal = Parameter(inVar.minFn)
        intervalSize = Parameter(lambda: inVar.rangeFn() / ntiles)
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

        regionVar = inVar.mesh.add_variable(1)
        polygon = inShape.morph(inVar.mesh)
        boolFn = fn.branching.conditional([
            (polygon, 1),
            (True, 0),
            ])
        regionVar.data[:] = boolFn.evaluate(inVar.mesh)

        nullVal = [np.nan for dim in range(inVar.varDim)]
        var = fn.branching.conditional([
            (regionVar > 0., inVar),
            (True, nullVal),
            ])

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

class Surface(Function):

    opTag = 'Surface'

    def __init__(self, inVar, *args, surface = 'inner', **kwargs):

        inVar = convert(inVar)

        if inVar.substrate is None:
            raise Exception
        if not hasattr(inVar, 'mesh'):
            raise Exception

        self._surface = \
            inVar.mesh.meshUtils.surfaces[surface]

        var = inVar.mesh.add_variable(
            inVar.varDim,
            inVar.dType
            )

        self.stringVariants = {'surface': surface}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self.var.data[:] = \
            [np.nan for dim in range(self.inVar.varDim)]
        self.var.data[self._surface] = \
            np.round(
                self.inVar.evaluate(
                    self.inVar.mesh.data[self._surface],
                    lazy = True
                    ),
                6
                )

    @staticmethod
    def volume(*args, **kwargs):
        return Surface(*args, surface = 'volume', **kwargs)

    @staticmethod
    def inner(*args, **kwargs):
        return Surface(*args, surface = 'inner', **kwargs)

    @staticmethod
    def outer(*args, **kwargs):
        return Surface(*args, surface = 'outer', **kwargs)

    @staticmethod
    def left(*args, **kwargs):
        return Surface(*args, surface = 'left', **kwargs)

    @staticmethod
    def right(*args, **kwargs):
        return Surface(*args, surface = 'right', **kwargs)

    @staticmethod
    def front(*args, **kwargs):
        return Surface(*args, surface = 'front', **kwargs)

    @staticmethod
    def back(*args, **kwargs):
        return Surface(*args, surface = 'back', **kwargs)

class Normalise(Function):

    opTag = 'Normalise'

    def __init__(self, baseVar, normVar, *args, **kwargs):

        baseVar, normVar = inVars = convert(baseVar, normVar)

        inMins = Parameter(baseVar.minFn)
        inRanges = Parameter(baseVar.rangeFn)
        normMins = Parameter(normVar.minFn)
        normRanges = Parameter(normVar.rangeFn)

        var = (baseVar - inMins) / inRanges * normRanges + normMins

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = [inMins, inRanges, normMins, normRanges]
        self.var = var

        super().__init__(**kwargs)
