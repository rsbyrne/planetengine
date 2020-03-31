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
            check = 50,
            x = 'chron',
            y = ('Nu', 'theta_av'),
            tolerance = 1e-3
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
        half = metric[np.where(chron > np.max(chron) - np.ptp(chron) / 2.)]
        return np.ptp(half) < self.tolerance * np.abs(np.average(half))

CLASS = Flat
