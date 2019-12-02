from planetengine import fieldops
from planetengine import mapping
from planetengine import utilities
from planetengine.IC import IC

def build(*args, **kwargs):
    built = Load(*args, **kwargs)
    return built

class Load(IC):

    name = 'load'

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
            script = __file__,
            evaluate = evaluate
            )
