from underworld import function as fn
import numpy as np

class IC:

    def __init__(
            self,
            *args,
            shapes = None
            ):

        # HOUSEKEEPING: this should always be here
        self.script = __file__
        self.inputs = {}

        if shapes is None:
            shapes = args
        self.inputs['shapes'] = shapes

        self.polygons = [(0, fn.misc.constant(True))]
        for val, vertices in shapes:
            array = np.array(vertices)
            self.polygons.append(
                (val, fn.shape.Polygon(array))
                )

    def evaluate(self, coordArray):
        outArray = np.zeros(coordArray.shape, dtype=np.int)
        for val, polygonFn in self.polygons:
            outArray = np.where(
                polygonFn.evaluate(coordArray),
                [val],
                outArray
                )
        return outArray