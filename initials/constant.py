import numpy as np
from planetengine.initials import IC

class Constant(IC):

    species = 'constant'

    def __init__(
            self,
            value = 0.
            ):

        self.value = value

        super().__init__(
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

### IMPORTANT ###
# from everest.builts import make_buildFn
CLASS = Constant
build = CLASS.build
