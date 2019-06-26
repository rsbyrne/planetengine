import numpy as np

from ..mapping import box
from ..utilities import copyField

class IC:

    def __init__(
            self,
            pert = 0.2,
            freq = 1.,
            phase = 0.
            ):

        self.inputs = locals().copy()
        del self.inputs['self']
        self.script = __file__

        self.valRange = (0., 1.)

        self.freq = freq
        self.phase = phase
        self.pert = pert

    def evaluate(self, coordArray):
        boxLength = 1.
        boxHeight = 1.
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

#     def apply(self, variable, boxDims = None):
#         try:
#             mesh = variable.mesh
#             meshVar = variable
#         except:
#             try:
#                 mesh = variable.swarm.mesh
#                 meshVar = mesh.add_variable(variable.count)
#             except:
#                 raise Exception("Did not recognise input variable.")
#         if boxDims is None:
#             boxDims = self.boxDims
#         coordArray = box(mesh, boxDims = boxDims)
#         meshVar.data[:] = self.sinusoidal_IC(coordArray)
#         if not meshVar is variable:
#             copyField(meshVar, variable)
#             del meshVar