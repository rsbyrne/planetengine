from . import Final
from ..observers import Thermo
from .. import analysis as pan

class Harmonic(Final):

    def __init__(self,
            system,
            sampleFactor = 0.5,
            interpKind = 'cubic',
            **kwargs
            ):

        self.observer = Thermo(system, **kwargs)

        self.system, self.sampleFactor, self.interpKind = \
            system, sampleFactor, interpKind

        super().__init__()

    def _zone_fn(self):
        chrons, Nus = self.observer['chron', 'Nu']
        ichrons, iNus = pan.time_smooth(
            chrons,
            Nus,
            self.sampleFactor,
            kind = self.interpKind
            )
