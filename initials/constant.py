import numpy as np
from planetengine._IC import IC

def build(*args, name = None, **kwargs):
    built = Constant(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Constant(IC):

    script = __file__

    def __init__(
            self,
            *args,
            value = 0.,
            **kwargs
            ):

        inputs = locals().copy()

        self.value = value

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script,
            evaluate = self.evaluate
            )

    def _get_ICdata(self, *args, **kwargs):
        return self._get_ICdata(*args, **kwargs)
    def evaluate(self, *args, **kwargs):
        return np.array([self.value])
    def _apply(self, var):
        var.value = self.value
    def apply(self, var):
        self._apply(var)
