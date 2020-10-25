from collections import OrderedDict

from everest.frames._observer import Observer
from grouper import Grouper

from planetengine.exceptions import *

class ObserverException(PlanetEngineException):
    pass
class ObserverMissingAsset(
        ObserverException,
        MissingAsset,
        ):
    pass

class PlanetObserver(Observer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _observer_construct(self, subject, inputs):
        observer = super()._observer_construct(subject, inputs)
        constructed = self._construct(subject.observables, inputs)
        if not 'analysers' in constructed:
            raise ObserverMissingAsset
        def evaluate():
            return OrderedDict(
                (k, an.evaluate())
                    for k, an in constructed['analysers'].items()
                )
        constructed['evaluate'] = evaluate
        observer.update(constructed, silent = True)
        return observer

    @staticmethod
    def _construct(observables, inputs):
        raise ObserverMissingAsset

from .thermo import Thermo
