from underworld import function as fn

from . import _function
from . import _convert

class Operations(_function.Function):

    opTag = 'Operation'

    uwNamesToFns = {
        'pow': fn.math.pow,
        'abs': fn.math.abs,
        'cosh': fn.math.cosh,
        'acosh': fn.math.acosh,
        'tan': fn.math.tan,
        'asin': fn.math.asin,
        'log': fn.math.log,
        'atanh': fn.math.atanh,
        'sqrt': fn.math.sqrt,
        'abs': fn.math.abs,
        'log10': fn.math.log10,
        'sin': fn.math.sin,
        'asinh': fn.math.asinh,
        'log2': fn.math.log2,
        'atan': fn.math.atan,
        'sinh': fn.math.sinh,
        'cos': fn.math.cos,
        'tanh': fn.math.tanh,
        'erf': fn.math.erf,
        'erfc': fn.math.erfc,
        'exp': fn.math.exp,
        'acos': fn.math.acos,
        'dot': fn.math.dot,
        'add': fn._function.add,
        'subtract': fn._function.subtract,
        'multiply': fn._function.multiply,
        'divide': fn._function.divide,
        'greater': fn._function.greater,
        'greater_equal': fn._function.greater_equal,
        'less': fn._function.less,
        'less_equal': fn._function.less_equal,
        'logical_and': fn._function.logical_and,
        'logical_or': fn._function.logical_or,
        'logical_xor': fn._function.logical_xor,
        'input': fn._function.input,
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

    @staticmethod
    def pow(*args, **kwargs):
        return Operations(*args, uwop = 'pow', **kwargs)

    @staticmethod
    def abs(*args, **kwargs):
        return Operations(*args, uwop = 'abs', **kwargs)

    @staticmethod
    def cosh(*args, **kwargs):
        return Operations(*args, uwop = 'cosh', **kwargs)

    @staticmethod
    def acosh(*args, **kwargs):
        return Operations(*args, uwop = 'acosh', **kwargs)

    @staticmethod
    def tan(*args, **kwargs):
        return Operations(*args, uwop = 'tan', **kwargs)

    @staticmethod
    def asin(*args, **kwargs):
        return Operations(*args, uwop = 'asin', **kwargs)

    @staticmethod
    def log(*args, **kwargs):
        return Operations(*args, uwop = 'log', **kwargs)

    @staticmethod
    def atanh(*args, **kwargs):
        return Operations(*args, uwop = 'atanh', **kwargs)

    @staticmethod
    def sqrt(*args, **kwargs):
        return Operations(*args, uwop = 'sqrt', **kwargs)

    @staticmethod
    def abs(*args, **kwargs):
        return Operations(*args, uwop = 'abs', **kwargs)

    @staticmethod
    def log10(*args, **kwargs):
        return Operations(*args, uwop = 'log10', **kwargs)

    @staticmethod
    def sin(*args, **kwargs):
        return Operations(*args, uwop = 'sin', **kwargs)

    @staticmethod
    def asinh(*args, **kwargs):
        return Operations(*args, uwop = 'asinh', **kwargs)

    @staticmethod
    def log2(*args, **kwargs):
        return Operations(*args, uwop = 'log2', **kwargs)

    @staticmethod
    def atan(*args, **kwargs):
        return Operations(*args, uwop = 'atan', **kwargs)

    @staticmethod
    def sinh(*args, **kwargs):
        return Operations(*args, uwop = 'sinh', **kwargs)

    @staticmethod
    def cos(*args, **kwargs):
        return Operations(*args, uwop = 'cos', **kwargs)

    @staticmethod
    def tanh(*args, **kwargs):
        return Operations(*args, uwop = 'tanh', **kwargs)

    @staticmethod
    def erf(*args, **kwargs):
        return Operations(*args, uwop = 'erf', **kwargs)

    @staticmethod
    def erfc(*args, **kwargs):
        return Operations(*args, uwop = 'erfc', **kwargs)

    @staticmethod
    def exp(*args, **kwargs):
        return Operations(*args, uwop = 'exp', **kwargs)

    @staticmethod
    def acos(*args, **kwargs):
        return Operations(*args, uwop = 'acos', **kwargs)

    @staticmethod
    def dot(*args, **kwargs):
        return Operations(*args, uwop = 'dot', **kwargs)

    @staticmethod
    def add(*args, **kwargs):
        return Operations(*args, uwop = 'add', **kwargs)

    @staticmethod
    def subtract(*args, **kwargs):
        return Operations(*args, uwop = 'subtract', **kwargs)

    @staticmethod
    def multiply(*args, **kwargs):
        return Operations(*args, uwop = 'multiply', **kwargs)

    @staticmethod
    def divide(*args, **kwargs):
        return Operations(*args, uwop = 'divide', **kwargs)

    @staticmethod
    def greater(*args, **kwargs):
        return Operations(*args, uwop = 'greater', **kwargs)

    @staticmethod
    def greater_equal(*args, **kwargs):
        return Operations(*args, uwop = 'greater_equal', **kwargs)

    @staticmethod
    def less(*args, **kwargs):
        return Operations(*args, uwop = 'less', **kwargs)

    @staticmethod
    def less_equal(*args, **kwargs):
        return Operations(*args, uwop = 'less_equal', **kwargs)

    @staticmethod
    def logical_and(*args, **kwargs):
        return Operations(*args, uwop = 'logical_and', **kwargs)

    @staticmethod
    def logical_or(*args, **kwargs):
        return Operations(*args, uwop = 'logical_or', **kwargs)

    @staticmethod
    def logical_xor(*args, **kwargs):
        return Operations(*args, uwop = 'logical_xor', **kwargs)

    @staticmethod
    def input(*args, **kwargs):
        return Operations(*args, uwop = 'input', **kwargs)
