import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler

class Observer(Counter, Cycler):

    _swapscript = '''from planetengine.observers import Observer as CLASS'''

    def __init__(self, **kwargs):

        # Expects:
        # self.observee
        # self.analysers

        self.check = lambda: True

        super().__init__(**kwargs)

        # Producer attributes:
        self._outFns.append(self._out)
        self.outkeys.extend(sorted(self.analysers.keys()))

        # Cycler attributes:
        self._cycle_fns.append(self._observer_cycle)

        # Local attributes:
        self.allDict = {
            'count': self.count,
            **self.analysers
            }
        self._max_keylen = max([len(key) for key in self.outkeys])

    def set_freq(self, condition):
        self.check = condition

    def _observer_cycle(self):
        self.count.value = self.observee.count.value
        if self.check():
            self.store()

    def _out(self):
        for name, analyser in sorted(self.analysers.items()):
            yield analyser.evaluate()

    def __str__(self):
        return '\n'.join([
            key.rjust(self._max_keylen) + ': ' + str(self.allDict[key]) \
                for key in self.outkeys
            ])
