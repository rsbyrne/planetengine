from underworld import function as fn
import numpy as np
from planetengine.IC import IC

def build(*args, **kwargs):
    built = Extents(*args, **kwargs)
    return built

class Extents(IC):

    def __init__(
            self,
            shapes = None
            ):

        inputs = locals().copy()

        polygons = [(0,fn.misc.constant(True))]
        for val, vertices in shapes:
            polygons.append(
                (val,fn.shape.Polygon(vertices))
                )

        def evaluate(coordArray):
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

        super().__init__(
            inputs = inputs,
            script = __file__,
            evaluate = evaluate
            )
