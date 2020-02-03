from planetengine import fieldops
from planetengine import mapping
from planetengine import utilities
from planetengine.initials import IC

class Copy(IC):

    def _process_inputs(inputs):
        realCount = inputs['real'].count()
        if not inputs['_count'] is None:
            if not realCount == inputs['_count']:
                raise Exception
        del inputs['_count']
        inputs['count'] = realCount

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

CLASS = Copy
build, get = CLASS.build, CLASS.get
