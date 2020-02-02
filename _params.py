from everest.builts._basket import Basket

class Params(Basket):
    from .params import __file__ as _file_
    @staticmethod
    def _process_inputs(inputs):
        for key, val in sorted(inputs.items()):
            if not type(val) is float:
                inputs[key] = float(val)
    def __init__(self, **kwargs):
        super().__init__()
