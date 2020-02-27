from planetengine.observers import Observer
from planetengine.functions import integral, gradient

class Thermo(Observer):

    def __init__(self,
            observee,
            key = 'temperatureField',
            **kwargs
            ):

        analysers = dict()
        field = observee.locals[key]

        baseInt = integral.inner(field)
        radGrad = gradient.rad(field)
        surfInt = integral.outer(radGrad)
        analysers['Nu'] = surfInt / baseInt

        analysers['avT'] = integral.volume(field)

        self.observee, self.analysers = observee, analysers

        super().__init__(**kwargs)

CLASS = Thermo
