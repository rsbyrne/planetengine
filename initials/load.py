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
            varName = None
            ):

        inputs = locals().copy()

        var = system.varsOfState[varName]

        def evaluate(coordArray):
            outArr = fieldops.safe_box_evaluate(var, coordArray)
            return outArr

        super().__init__(
            inputs = inputs,
            script = __file__,
            evaluate = evaluate
            )
