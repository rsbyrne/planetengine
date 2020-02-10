from underworld import function as fn
import numpy as np
from planetengine.initials import IC

class Extents(IC):

    script = __file__

    def __init__(
            self,
            shapes = None,
            **kwargs
            ):

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

        super().__init__(evaluate, **kwargs)

CLASS = Extents
build, get = CLASS.build, CLASS.get
