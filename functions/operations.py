from underworld import function as _fn

from . import _function
from . import _convert
from ._construct import _construct as _master_construct

def _construct(*args, **kwargs):
    func = _master_construct(Operations, *args, **kwargs)
    return func

class Operations(_function.Function):

    opTag = 'Operation'

    uwNamesToFns = {
        'pow': _fn.math.pow,
        'abs': _fn.math.abs,
        'cosh': _fn.math.cosh,
        'acosh': _fn.math.acosh,
        'tan': _fn.math.tan,
        'asin': _fn.math.asin,
        'log': _fn.math.log,
        'atanh': _fn.math.atanh,
        'sqrt': _fn.math.sqrt,
        'abs': _fn.math.abs,
        'log10': _fn.math.log10,
        'sin': _fn.math.sin,
        'asinh': _fn.math.asinh,
        'log2': _fn.math.log2,
        'atan': _fn.math.atan,
        'sinh': _fn.math.sinh,
        'cos': _fn.math.cos,
        'tanh': _fn.math.tanh,
        'erf': _fn.math.erf,
        'erfc': _fn.math.erfc,
        'exp': _fn.math.exp,
        'acos': _fn.math.acos,
        'dot': _fn.math.dot,
        'add': _fn._function.add,
        'subtract': _fn._function.subtract,
        'multiply': _fn._function.multiply,
        'divide': _fn._function.divide,
        'greater': _fn._function.greater,
        'greater_equal': _fn._function.greater_equal,
        'less': _fn._function.less,
        'less_equal': _fn._function.less_equal,
        'logical_and': _fn._function.logical_and,
        'logical_or': _fn._function.logical_or,
        'logical_xor': _fn._function.logical_xor,
        'input': _fn._function.input,
        }

    def __init__(self, *args, uwop = None, **kwargs):

        if not uwop in self.uwNamesToFns:
            raise Exception
        opFn = self.uwNamesToFns[uwop]

        var = opFn(*args)

        inVars = _convert.convert(args)

        self.stringVariants = {'uwop': uwop}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

def default(*args, **kwargs):
    return _construct(*args, **kwargs)

def pow(*args, **kwargs):
    return _construct(*args, uwop = 'pow', **kwargs)

def abs(*args, **kwargs):
    return _construct(*args, uwop = 'abs', **kwargs)

def cosh(*args, **kwargs):
    return _construct(*args, uwop = 'cosh', **kwargs)

def acosh(*args, **kwargs):
    return _construct(*args, uwop = 'acosh', **kwargs)

def tan(*args, **kwargs):
    return _construct(*args, uwop = 'tan', **kwargs)

def asin(*args, **kwargs):
    return _construct(*args, uwop = 'asin', **kwargs)

def log(*args, **kwargs):
    return _construct(*args, uwop = 'log', **kwargs)

def atanh(*args, **kwargs):
    return _construct(*args, uwop = 'atanh', **kwargs)

def sqrt(*args, **kwargs):
    return _construct(*args, uwop = 'sqrt', **kwargs)

def abs(*args, **kwargs):
    return _construct(*args, uwop = 'abs', **kwargs)

def log10(*args, **kwargs):
    return _construct(*args, uwop = 'log10', **kwargs)

def sin(*args, **kwargs):
    return _construct(*args, uwop = 'sin', **kwargs)

def asinh(*args, **kwargs):
    return _construct(*args, uwop = 'asinh', **kwargs)

def log2(*args, **kwargs):
    return _construct(*args, uwop = 'log2', **kwargs)

def atan(*args, **kwargs):
    return _construct(*args, uwop = 'atan', **kwargs)

def sinh(*args, **kwargs):
    return _construct(*args, uwop = 'sinh', **kwargs)

def cos(*args, **kwargs):
    return _construct(*args, uwop = 'cos', **kwargs)

def tanh(*args, **kwargs):
    return _construct(*args, uwop = 'tanh', **kwargs)

def erf(*args, **kwargs):
    return _construct(*args, uwop = 'erf', **kwargs)

def erfc(*args, **kwargs):
    return _construct(*args, uwop = 'erfc', **kwargs)

def exp(*args, **kwargs):
    return _construct(*args, uwop = 'exp', **kwargs)

def acos(*args, **kwargs):
    return _construct(*args, uwop = 'acos', **kwargs)

def dot(*args, **kwargs):
    return _construct(*args, uwop = 'dot', **kwargs)

def add(*args, **kwargs):
    return _construct(*args, uwop = 'add', **kwargs)

def subtract(*args, **kwargs):
    return _construct(*args, uwop = 'subtract', **kwargs)

def multiply(*args, **kwargs):
    return _construct(*args, uwop = 'multiply', **kwargs)

def divide(*args, **kwargs):
    return _construct(*args, uwop = 'divide', **kwargs)

def greater(*args, **kwargs):
    return _construct(*args, uwop = 'greater', **kwargs)

def greater_equal(*args, **kwargs):
    return _construct(*args, uwop = 'greater_equal', **kwargs)

def less(*args, **kwargs):
    return _construct(*args, uwop = 'less', **kwargs)

def less_equal(*args, **kwargs):
    return _construct(*args, uwop = 'less_equal', **kwargs)

def logical_and(*args, **kwargs):
    return _construct(*args, uwop = 'logical_and', **kwargs)

def logical_or(*args, **kwargs):
    return _construct(*args, uwop = 'logical_or', **kwargs)

def logical_xor(*args, **kwargs):
    return _construct(*args, uwop = 'logical_xor', **kwargs)

def input(*args, **kwargs):
    return _construct(*args, uwop = 'input', **kwargs)
