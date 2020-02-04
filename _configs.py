from everest.builts.vector import Vector
from everest.builts._applier import Applier
from .initials import IC as ICclass
from .exceptions import PlanetEngineException

class InsufficientConfigsError(PlanetEngineException):
    '''Configs keys must match varsOfState keys.'''
    pass

class Configs(Vector, Applier):
    from .configs import __file__ as _file_
    @staticmethod
    def _process_inputs(inputs):
        for key, val in sorted(inputs.items()):
            if not isinstance(val, ICclass):
                raise TypeError
    def __init__(self, **kwargs):
        super().__init__()
        def apply(case):
            if not case.varsOfState.keys() == self.inputs.keys():
                raise InsufficientConfigsError(
                    case.varsOfState.keys(),
                    self.inputs.keys()
                    )
            for key, IC in sorted(self.inputs.items()):
                IC(case.varsOfState[key])
        self._apply_fns.append(apply)
