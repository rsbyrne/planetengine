from everest.builts.vector import Vector
from .initials import IC as ICclass

from everest.builts._vector import Vector

class Configs(Vector):
    from .configs import __file__ as _file_
    @staticmethod
    def _process_inputs(inputs):
        for key, val in sorted(inputs.items()):
            if not isinstance(val, ICclass):
                raise TypeError
    def __init__(self, **kwargs):
        super().__init__()
