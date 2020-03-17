from . import Final
from ..observers import Thermo

class Steady(Final):

    def __init__(self,
            system,
            **kwargs
            ):
        self.observer = Thermo(system, **kwargs)
        super().__init__()
