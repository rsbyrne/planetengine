import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler
from everest.builts.states import State
from everest.builts.states.threshold import Threshold
from everest.builts.condition import Condition
from everest.writer import LinkTo

class Observer(Counter, Cycler):

    def __init__(self, **kwargs):

        # Expects:
        # self.observee
        # self.analysers

        self.check = lambda: False

        super().__init__(observee = LinkTo(self.observee), **kwargs)

        # Producer attributes:
        self._outFns.append(self._out)
        self.analysers['chron'] = self.observee.chron
        self.outkeys.extend(sorted(self.analysers.keys()))

        # Cycler attributes:
        self._cycle_fns.append(self._observer_cycle)

        # Counter attributes:
        self._count_update_fns.append(self.update)

    def set_freq(self, freq):
        if isinstance(freq, Condition):
            condition = freq
        else:
            if isinstance(freq, State):
                state = freq
            else:
                if type(freq) is int: prop = 'count'
                else: raise TypeError
                state = Threshold(
                    prop = prop,
                    op = 'mod',
                    val = freq,
                    inv = True
                    )
            condition = Condition(state, self.observee)
        self.check = condition

    def update(self):
        self.count.value = self.observee.count.value

    def _observer_cycle(self):
        self.update()
        if self.check:
            self.store()

    def _out(self):
        self.update()
        for name, analyser in sorted(self.analysers.items()):
            yield analyser.evaluate()

    def __str__(self):
        allDict = {
            'count': self.count,
            **self.analysers
            }
        _max_keylen = max([len(key) for key in self.outkeys])
        return '\n'.join([
            key.rjust(_max_keylen) + ': ' + str(allDict[key]) \
                for key in self.outkeys
            ])
