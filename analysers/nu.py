from planetengine.analysers import Analyser
from planetengine.functions import integral, gradient

class Nu(Analyser):

    script = __file__

    def __init__(self,
            analysee,
            key = 'temperatureField',
            **kwargs
            ):

        field = analysee.locals[key]
        baseInt = integral.inner(field)
        radGrad = gradient.rad(field)
        surfInt = integral.outer(radGrad)
        Nu = surfInt / baseInt

        self.op = Nu

        super().__init__(**kwargs)

    def _evaluate(self):
        return self.op.evaluate()[0][0]
