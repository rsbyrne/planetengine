from underworld import function as fn
from planetengine.mapping import box
from planetengine.utilities import setboundaries
import numpy as np

class IC:
    '''
    Takes inputs in the form of a tuple (not list!)
    of tuples. For each sub-tuple:
    (value, tuple of tuples)
    The interior tuples of tuples are turned into Underworld
    polygon functions and evaluated for the input variable.
    '''

    def __init__(
            self,
            *args,
            shapes = None,
            default = 0,
            boxDims = ((0., 1.), (0., 1.)),
            boundaries = ('.', '.', '.', '.')
            ):

        # HOUSEKEEPING: this should always be here
        boxDims = tuple(
            [tuple([float(inner) for inner in outer]) for outer in boxDims]
            )
        self.inputs = locals().copy()
        del self.inputs['self']
        del self.inputs['args']
        self.script = __file__

        if shapes is None:
            shapes = args
            self.inputs['shapes'] = shapes

        self.boxDims = boxDims
        self.boundaries = boundaries
        if type(boundaries) == list:
            boundaries = tuple(boundaries)
            self.inputs['boundaries'] = boundaries

        self.polygons = [(default, fn.misc.constant(True))]
        for val, vertices in shapes:
            array = np.array(vertices)
            self.polygons.append(
                (val, fn.shape.Polygon(array))
                )

    def initial_extents(self, coordArray, variableShape):
        ICarray = np.zeros(variableShape, dtype=np.int)
        for val, polygonFn in self.polygons:
            ICarray = np.where(
                polygonFn.evaluate(coordArray),
                [val],
                ICarray
                )
        return ICarray

    def apply(self, variable):
        try:
            mesh = variable.mesh
            coords = mesh.data
        except:
            try:
                mesh = variable.swarm.mesh
                coords = variable.swarm.particleCoordinates.data
            except:
                raise Exception("Did not recognise input variable.")
        coordArray = box(mesh, coords, boxDims = self.boxDims)
        variable.data[:] = self.initial_extents(
            coordArray, variable.data.shape
            )
        try:
            setboundaries(variable, self.boundaries)
        except:
            pass
