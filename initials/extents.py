from underworld import function as _fn
import numpy as np
from planetengine._IC import IC

def build(*args, name = None, **kwargs):
    built = Extents(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Extents(IC):

    script = __file__

    def __init__(
            self,
            *args,
            shapes = None,
            **kwargs
            ):

        # HOUSEKEEPING: this should always be here
        inputs = locals().copy()

        self.polygons = [(0, _fn.misc.constant(True))]
        for val, vertices in shapes:
            self.polygons.append(
                (val, _fn.shape.Polygon(vertices))
                )

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script,
            evaluate = self.evaluate
            )

    def evaluate(self, coordArray):
        outArray = np.zeros(
            (coordArray.shape[0], 1), dtype = np.int
            )
        for val, polygonFn in self.polygons:
            outArray = np.where(
                polygonFn.evaluate(coordArray),
                val,
                outArray
                )
        return outArray
