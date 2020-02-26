from planetengine.analysers import Analyser
from planetengine.functions import operations, integral, component

class VRMS(Analyser):

    script = __file__

    def __init__(self,
            analysee,
            key = 'velocityField',
            name = None,
            **kwargs
            ):

        field = analysee.locals[key]
        VRMS = operations.sqrt(integral.volume(component.sq(field)))

        self.op = VRMS

        super().__init__(**kwargs)

    def _evaluate(self):
        return self.op.evaluate()[0][0]

CLASS = VRMS
