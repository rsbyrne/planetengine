from planetengine.mapping import box
from planetengine.utilities import copyField
from planetengine.utilities import setboundaries
import numpy as np

class IC:

    def __init__(
            self,
            pert = 0.2,
            freq = 1.,
            valRange = (0., 1.),
            phase = 0.,
            boxDims = ((0., 1.), (0., 1.)),
            boundaries = None,
            ):

        boxDims = tuple(
            [tuple([float(inner) for inner in outer]) for outer in boxDims]
            )
        valRange = tuple([float(i) for i in valRange])
        phase = float(phase)
        freq = float(freq)
        pert = float(pert)

        self.inputs = locals().copy()
        del self.inputs['self']
        self.script = __file__

        if boundaries is None:
            boundaries = (valRange[0], valRange[1], '.', '.')
        elif type(boundaries) == list:
            boundaries = tuple(boundaries)
        self.inputs['boundaries'] = boundaries

        self.freq = freq
        self.valRange = valRange
        self.phase = phase
        self.pert = pert
        self.boxDims = boxDims
        self.boundaries = boundaries

    def sinusoidal_IC(self, coordArray):
        boxLength = self.boxDims[0][1] - self.boxDims[0][0]
        boxHeight = self.boxDims[1][1] - self.boxDims[1][0]
        valMin, valMax = self.valRange
        deltaVal = self.valRange[1] - self.valRange[0]
        pertArray = \
            self.pert \
            * np.cos(np.pi * (self.phase + self.freq * coordArray[:,0])) \
            * np.sin(np.pi * coordArray[:,1])
        outArray = valMin + deltaVal * (boxHeight - coordArray[:,1]) + pertArray
        outArray = np.clip(outArray, valMin, valMax)
        outArray = np.array([[item] for item in outArray])
        return outArray

    def apply(self, variable):
        try:
            mesh = variable.mesh
            meshVar = variable
        except:
            try:
                mesh = variable.swarm.mesh
                meshVar = mesh.add_variable(variable.count)
            except:
                raise Exception("Did not recognise input variable.")
        coordArray = box(mesh, boxDims = self.boxDims)
        meshVar.data[:] = self.sinusoidal_IC(coordArray)
        setboundaries(meshVar, self.boundaries)
        if not meshVar is variable:
            copyField(meshVar, variable)
            del meshVar