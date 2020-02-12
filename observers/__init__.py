import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler

class Observer(Counter, Cycler):

    script = '''_script_from planetengine.observers import Observer as CLASS'''

    def __init__(self,
            observee,
            analyserClasses = [],
            **kwargs
            ):

        observeDict = dict()
        for analyserClass in analyserClasses:
            analyser = analyserClass(observee)
            observeDict[analyser.dataName] = analyser

        super().__init__(**kwargs)

        # Producer attributes:
        self._outFns.append(self._out)
        self.outkeys.extend(['chron', *sorted(observeDict.keys())])
        self._pre_store_fns.append(self._observer_pre_store_fn)

        # Cycler attributes:
        self._cycle_fns.append(self.store)

        # Local attributes:
        self.allDict = {
            'count': observee.count,
            'chron': observee.chron,
            **observeDict
            }
        self._max_keylen = max([len(key) for key in self.outkeys])
        self.observeDict = observeDict
        self.observee = observee

    def _observer_pre_store_fn(self):
        self.count.value = self.observee.count.value

    def _out(self):
        yield np.array(self.observee.chron())
        for name, analyser in sorted(self.observeDict.items()):
            yield analyser()

    def __str__(self):
        return '\n'.join([
            key.rjust(self._max_keylen) + ': ' + str(self.allDict[key]) \
                for key in self.outkeys
            ])
