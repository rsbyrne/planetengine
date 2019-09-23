class Reduction(PlanetVar):

    def __init__(self, *args, **kwargs):

        self.mesh = self.substrate = None

        sample_data = self.var.evaluate()
        self.dType = get_dType(sample_data)
        self.varType = 'red'
        self.meshUtils = None
        self.meshbased = False

        self._hashVars = self.inVars

        super().__init__(**kwargs)

class GetStat(Reduction):

    opTag = 'GetStat'

    def __init__(self, inVar, *args, stat = 'mins', **kwargs):

        if not stat in {'mins', 'maxs', 'ranges'}:
            raise Exception

        inVar = convert(inVar)

        if stat == 'mins':
            var = Parameter(inVar.minFn)
        elif stat == 'maxs':
            var = Parameter(inVar.maxFn)
        elif stat == 'ranges':
            var = Parameter(inVar.rangeFn)

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

        if isinstance(inVar, Reduction):
            raise Exception
        if type(inVar) == Surface:
            raise Exception(
                "Surface type not accepted; try Integral.auto method."
                )

        inVar = HandleNaN.zeroes(inVar)

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

    @staticmethod
    def auto(*args, **kwargs):
        inVar = convert(args[0])
        if type(inVar) == Surface:
            surface = inVar.stringVariants['surface']
            inVar = inVar.inVar
        else:
            surface = 'volume'
        return Integral(inVar, *args, surface = surface, **kwargs)
