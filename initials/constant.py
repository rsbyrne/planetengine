import numpy as np
from planetengine.IC import IC

def build(*args, **kwargs):
    built = Constant(*args, **kwargs)
    return built

class Constant(IC):

    def __init__(
            self,
            value = 0.
            ):

        inputs = locals().copy()

        self.value = value

        super().__init__(
            inputs = inputs,
            script = __file__,
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
