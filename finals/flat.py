import numpy as np

from window import analysis

from . import Final
from ..observers import Thermo

class Flat(Final):

    def __init__(self,
            system,
            observerClass = Thermo,
            observerKwargs = dict(),
            freq = 10,
            x = 'chron',
            y = ('Nu', 'temp_av'),
            tolerance = 1e-3,
            horizon = 0.1,
            check = 50,
            ):

        self.system = system
        self.observer = self.system.add_observer(
            observerClass,
            **observerKwargs
            )
        ignoreme = self.observer.add_freq(freq)
        self.x = x
        self.y = y if type(y) is tuple else (y,)
        self.tolerance = tolerance
        self.horizon = horizon

        super().__init__(check = check)

    def _zone_fn(self):
        chron = self.observer.data[self.x]
        metrics = self.observer.data[self.y]
        if len(chron) > 10:
            return all([self._flat_condition(chron, m) for m in metrics])
        else:
            return False

    def _flat_condition(self, chron, metric):
        chron, metric = analysis.time_smooth(chron, metric, sampleFactor = 2.)
        chron, metric = chron[1:-1], metric[1:-1]
        indices = np.where(chron > np.max(chron) - self.horizon * np.ptp(chron))
        interval = metric[indices]
        return np.ptp(interval) < self.tolerance * np.abs(np.average(interval))

CLASS = Flat
