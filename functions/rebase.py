from . import _function
from . import _convert
from . import _basetypes
from ._construct import _construct as _master_construct

def _construct(*args, **kwargs):
    func = _master_construct(Rebase, *args, **kwargs)
    return func

class Rebase(_function.Function):

    opTag = 'Rebase'

    def __init__(self, inVar, refVar, *args, **kwargs):

        inVar, refVar = inVars = _convert.convert(inVar, refVar)

        self.refVar = refVar

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = inVar.var

        super().__init__(**kwargs)

    def scaleFn(self):
        if not hasattr(self, '_scaleFn'):
            self._set_summary_stats()
        scales = self._scaleFn()
        ref = self.refVar.evaluate()
        outs = []
        for dim in range(len(scales)):
            maxVal = max([abs(item - ref) for item in scales[dim]])
            outs.append([-maxVal, maxVal])
        return outs

def default(*args, **kwargs):
    return _construct(*args, **kwargs)

def zero(baseVar, *args, **kwargs):
    return _construct(baseVar, 0., **kwargs)
