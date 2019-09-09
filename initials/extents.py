from underworld import function as fn
import numpy as np

def build(*args, **kwargs):
    return IC(*args, **kwargs)

class IC:

    def __init__(
            self,
            *args,
            shapes = None
            ):

        # HOUSEKEEPING: this should always be here
        self.scripts = [__file__,]
        self.inputs = {}

        if shapes is None:
            shapes = args
        self.inputs['shapes'] = shapes

        self.polygons = [(0, fn.misc.constant(True))]
        for val, vertices in shapes:
            self.polygons.append(
                (val, fn.shape.Polygon(vertices))
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
