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
