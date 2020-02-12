import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler

class Analyser:
    def __init__(self):
        pass

class Observer(Counter, Cycler):

    def __init__(self,
            observee,
            observeDict,
            **kwargs
            ):

        self.observee = observee
        self.observeDict = observeDict

        super().__init__(**kwargs)

        self._outkeys = ['chron', *sorted(self.observeDict.keys())]

        # Producer attributes:
        self._outFns.append(self._out)
        self.outkeys.extend(self._outkeys)

        # Cycler attributes:
        self._cycle_fns.append(self.store)

    def _out(self):
        yield np.array(self.chron())
        for name, analyser in sorted(self.observeDict.items()):
            yield analyser()
