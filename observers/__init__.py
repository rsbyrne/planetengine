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
        # self.visVars

        self.check = lambda: False

        super().__init__(observee = LinkTo(self.observee), **kwargs)

        self.fig = QuickFig(*self.visVars)

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

    def report(self):
        outs = self.out()
        outkeys = self.outkeys
        def dot_aligned(seq):
            snums = [str(n) for n in seq]
            dots = [len(s.split('.', 1)[0]) for s in snums]
            m = max(dots)
            return [' '*(m - d) + s for s, d in zip(snums, dots)]
        names, datas = [], []
        for name, data in zip(outkeys, outs):
            if data.shape == ():
                if name == 'count':
                    val = str(int(data))
                else:
                    val = "{:.2f}".format(data)
                justname = name.ljust(max([len(key) for key in outkeys]))
                names.append(justname)
                datas.append(val)
        datas = dot_aligned(datas)
        outlist = [name + ' : ' + data for name, data in zip(names, datas)]
        outstr = '\n'.join(outlist)
        mpi.message(outstr)

from .basic import Basic
