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
