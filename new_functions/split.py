from . import _function
from . import _convert

class Split(_function.Function):

    opTag = 'Split'

    def __init__(self, inVar, *args, column = 0, **kwargs):

        inVar = _convert.convert(inVar)

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
