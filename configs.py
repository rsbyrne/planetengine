from everest.builts._basket import Basket
from everest.builts._applier import Applier
from planetengine.initials import IC
from planetengine.exceptions import PlanetEngineException

class InsufficientConfigsError(PlanetEngineException):
    '''Configs keys must match varsOfState keys.'''
    pass

class Configs(Basket, Applier):
    @staticmethod
    def _process_inputs(inputs):
        for key, val in sorted(inputs.items()):
            if not isinstance(val, IC):
                raise TypeError
    def __init__(self, **kwargs):
        super().__init__()
        def apply(case):
            if not case.varsOfState.keys() == self.inputs.keys():
                raise InsufficientConfigsError
            for key, IC in sorted(self.inputs.items()):
                IC(case.varsOfState[key])
        self._apply_fns.append(apply)

CLASS = Configs
build, get = CLASS.build, CLASS.get
