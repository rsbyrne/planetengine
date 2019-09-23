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
