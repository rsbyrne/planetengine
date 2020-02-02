from planetengine import fieldops
from planetengine import mapping
from planetengine import utilities
from planetengine.initials import IC

class Load(IC):

    def _process_inputs(inputs):
        realCount = inputs['real'].count()
        if inputs['_count'] is None:
            inputs['_count'] = realCount
        else:
            if not realCount == inputs['counts']:
                raise Exception

    def __init__(
            self,
            real = None,
            varName = None,
            _count = None
            ):

        var = real.varsOfState[varName]
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
            evaluate = evaluate
            )

CLASS = Load
build, get = CLASS.build, CLASS.get
