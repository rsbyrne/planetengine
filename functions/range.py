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
