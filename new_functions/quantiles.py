import numpy as np

from underworld import function as fn

from . import _function
from . import _convert
from . import _basetypes

class Quantiles(_function.Function):

    opTag = 'Quantiles'

    def __init__(self, inVar, *args, ntiles = 5, **kwargs):

        inVar = _convert.convert(inVar)

        # if not inVar.varDim == 1:
        #     raise Exception

        interval = _basetypes.Parameter(
            lambda: inVar.rangeFn() / ntiles
            )
        minVal = _basetypes.Parameter(
            inVar.minFn
            )

        clauses = []
        for ntile in range(1, ntiles):
            clause = (
                inVar <= minVal + interval * float(ntile),
                float(ntile)
                )
            clauses.append(clause)
        clauses.append(
            (True, float(ntiles))
            )
        rawvar = fn.branching.conditional(clauses)
        var = fn.branching.conditional([
            (inVar < np.inf, rawvar),
            (True, np.nan)
            ])

        self.stringVariants = {
            'ntiles': str(ntiles)
            }
        self.inVars = [inVar]
        self.parameters = [interval, minVal]
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def median(*args, **kwargs):
        return Quantiles(*args, ntiles = 2, **kwargs)

    @staticmethod
    def terciles(*args, **kwargs):
        return Quantiles(*args, ntiles = 3, **kwargs)

    @staticmethod
    def quartiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 4, **kwargs)

    @staticmethod
    def quintiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 5, **kwargs)

    @staticmethod
    def deciles(*args, **kwargs):
        return Quantiles(*args, ntiles = 10, **kwargs)

    @staticmethod
    def percentiles(*args, **kwargs):
        return Quantiles(*args, ntiles = 100, **kwargs)
