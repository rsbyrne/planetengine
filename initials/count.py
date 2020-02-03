from planetengine import fieldops
from planetengine import mapping
from planetengine import utilities
from planetengine.initials import IC

class Count(IC):

    def _process_inputs(inputs):
        realCount = inputs['real'].count()
        if not inputs['count'] is None:
            if not realCount == inputs['count']:
                raise Exception
        inputs['count'] = realCount

    def __init__(
            self,
            real = None,
            varName = None,
            count = None
            ):
        if not count is None:
            real.load(count)
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

CLASS = Count
build, get = CLASS.build, CLASS.get
