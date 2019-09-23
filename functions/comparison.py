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
