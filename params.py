from everest.builts._basket import Basket

class Params(Basket):
    @staticmethod
    def _process_inputs(inputs):
        for key, val in sorted(inputs.items()):
            if not type(val) is float:
                inputs[key] = float(val)
    def __init__(self, **kwargs):
        super().__init__()

CLASS = Params
build, get = CLASS.build, CLASS.get
