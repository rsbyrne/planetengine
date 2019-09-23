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
