from . import _planetvar

class BaseTypes(_planetvar.PlanetVar):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def evaluate(self, evalInput = None, **kwargs):
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    def __call__(self):
        return self.var

from ._constant import Constant
from ._variable import Variable
from ._parameter import Parameter
from ._shape import Shape
