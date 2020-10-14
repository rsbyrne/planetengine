from everest.builts._observer import Observer
from everest.utilities import Grouper

from planetengine.exceptions import \
    PlanetEngineException, MissingMethod

class ObserverException(PlanetEngineException):
    pass
class ObserverMissingMethod(
        ObserverException,
        MissingMethod,
        ):
    pass

class PlanetObserver(Observer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _observer_construct(self, observables):
        observer = super()._observer_construct(observables)
        constructed = self._construct(observables)
        if not 'evaluate' in constructed:
            raise ObserverMissingMethod
        observer.update(constructed, silent = True)
        return observer

    def _construct(self, observables):
        raise ObserverMissingMethod

from .thermo import Thermo
