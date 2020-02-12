from planetengine.analysers import Analyser
from planetengine.functions import gradient, integral

class Nu(Analyser):

    script = __file__

    def __init__(self,
            analysee,
            key = None,
            **kwargs
            ):
        if key is None: key = 'temperatureField'
        field = getattr(analysee.locals, key)
        baseInt = integral.inner(field)
        radGrad = gradient.rad(field)
        surfInt = integral.outer(radGrad)
        Nu = surfInt / baseInt
        self.evaluator = Nu
