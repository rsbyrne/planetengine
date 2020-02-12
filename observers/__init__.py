import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler
from everest.builts.condition import Condition

class Observer(Counter, Cycler):

    script = '''_script_from planetengine.observers import Observer as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        if type(inputs['checkFreq']) is int:
            from everest.builts.states.threshold import Threshold
            inputs['checkFreq'] = Threshold('count', 'mod', 10, inv = True)

    def __init__(self,
            observee,
            checkFreq = 10,
            analyserClasses = [],
            **kwargs
            ):

        observeDict = dict()
        for analyserClass in analyserClasses:
            analyser = analyserClass(observee)
            observeDict[analyser.dataName] = analyser

        chron = observee.chron

        super().__init__(**kwargs)

        # Producer attributes:
        self._outFns.append(self._out)
        self.outkeys.extend(['chron', *sorted(observeDict.keys())])

        # Cycler attributes:
        self._cycle_fns.append(self._observer_cycle)

        # Local attributes:
        self.allDict = {
            'count': self.count,
            'chron': chron,
            **observeDict
            }
        self._max_keylen = max([len(key) for key in self.outkeys])
        self.observeDict = observeDict
        self.observee = observee
        self.checkCondition = Condition(checkFreq, self)
        self.chron = chron

    def _observer_cycle(self):
        self.count.value = self.observee.count.value
        if self.checkCondition:
            self.store()

    def _out(self):
        yield np.array(self.chron())
        for name, analyser in sorted(self.observeDict.items()):
            yield analyser()

    def __str__(self):
        return '\n'.join([
            key.rjust(self._max_keylen) + ': ' + str(self.allDict[key]) \
                for key in self.outkeys
            ])
