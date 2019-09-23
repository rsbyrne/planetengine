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
