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
