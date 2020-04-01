import numpy as np

from window import analysis

from . import Final
from ..observers import Thermo

class Averages(Final):

    def __init__(self,
            system,
            observerClass = Thermo,
            observerKwargs = dict(),
            freq = 10,
            x = 'chron',
            y = ('Nu', 'theta_av'),
            tolerance = 1e-3,
            horizon = 1. / np.e,
            check = 50,
            minlength = 50
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
        self.minlength = minlength

        super().__init__(check = check)

    def _zone_fn(self):
        chron = self.observer.data[self.x]
        metrics = self.observer.data[self.y]
        if len(chron) > self.minlength:
            return all([self._final_condition(chron, m) for m in metrics])
        else:
            return False

    def _final_condition(self, chron, metric):
        chron, metric = analysis.time_smooth(chron, metric, sampleFactor = 2.)
        chron, metric = chron[1:-1], metric[1:-1]
        cutoff1 = np.max(chron) - self.horizon * np.ptp(chron)
        cutoff2 = np.max(chron) - self.horizon **2. * np.ptp(chron)
        av1 = np.average(metric[np.where(chron > cutoff1)])
        av2 = np.average(metric[np.where(chron > cutoff2)])
        return max([av1, av2]) / min([av1, av2]) <= 1. + self.tolerance

CLASS = Averages
