from underworld.function._function import Function as UWFn

from . import _function
from . import _convert
from ._construct import _construct as _master_construct

def _construct(*args, **kwargs):
    func = _master_construct(Vanilla, *args, **kwargs)
    return func

class Vanilla(_function.Function):

    opTag = 'Vanilla'

    def __init__(self, inVar, *args, **kwargs):

        var = UWFn.convert(inVar)

        if not hasattr(var, '_underlyingDataItems'):
            raise Exception
        if not len(var._underlyingDataItems) > 0:
            raise Exception

        inVars = _convert.convert(
            tuple(
                sorted(
                    var._underlyingDataItems
                    )
                )
            )

        self.stringVariants = {'UWhash': var.__hash__()}
        self.inVars = inVars
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return _construct(*args, **kwargs)
