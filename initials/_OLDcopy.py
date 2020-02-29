from .. import fieldops
from .. import mapping
from .. import utilities
from . import IC

class Copy(IC):

    def __init__(
            self,
            initialiseFn,
            varName,
            **kwargs
            ):

        def initialise():
            real = initialiseFn()
            var = real.varsOfState[varName]
            fromMesh = utilities.get_mesh(var)
            globalFromMesh = fieldops.get_global_var_data(fromMesh)
            globalFromField = fieldops.get_global_var_data(var)
            self.evalFromMesh = globalFromMesh
            self.evalFromField = globalFromField
            self.evalVar = var

        def evaluate(coordArray):
            outArr = fieldops.safe_box_evaluate(
                self.evalVar,
                coordArray,
                globalFromMesh = self.evalFromMesh,
                globalFromField = self.evalFromField
                )
            return outArr

        super().__init__(evaluate, initialise, **kwargs)
