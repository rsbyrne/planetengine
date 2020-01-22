from planetengine import fieldops
from planetengine import mapping
from planetengine import utilities
from planetengine.initials import IC

class Load(IC):

    species = 'load'

    def __init__(
            self,
            system = None,
            varName = None,
            count = None
            ):

        if count is None:
            count = system.count()
        else:
            system.load(count)

        inputs = locals().copy()

        var = system.varsOfState[varName]
        fromMesh = utilities.get_mesh(var)
        globalFromMesh = fieldops.get_global_var_data(fromMesh)
        globalFromField = fieldops.get_global_var_data(var)

        def evaluate(coordArray):
            outArr = fieldops.safe_box_evaluate(
                var,
                coordArray,
                globalFromMesh = globalFromMesh,
                globalFromField = globalFromField
                )
            return outArr

        super().__init__(
            inputs = inputs,
            evaluate = evaluate
            )

### IMPORTANT ###
from everest.builts import make_buildFn
CLASS = Load
build = make_buildFn(CLASS)
