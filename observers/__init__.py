import numpy as np

from everest.builts._counter import Counter
from everest.builts._cycler import Cycler
from everest.builts.states import State
from everest.builts.states.threshold import Threshold
from everest.builts.condition import Condition
from everest.writer import LinkTo
from everest import mpi

from planetengine.visualisation.quickfig import QuickFig

from ..utilities import _get_condition

class Observer(Counter, Cycler):

    @staticmethod
    def _process_inputs(inputs):
        observee = inputs['observee']
        if not observee.initialised:
            observee.initialise()
        return inputs

    def __init__(self, **kwargs):

        # Expects:
        # self.observee
        # self.analysers
        # self.visVars

        self.check = lambda: False

        # self.initialise, self.reset, self.load, \
        # self.iterate = \
        #     self.observee.initialise, self.observee.reset, \
        #     self.observee.load, self.observee.iterate, \

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
        self.check = _get_condition(self.observee, freq)

    def update(self):
        if not self.observee.initialised:
            self.observee.initialise()
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
                if type(data) in {np.int32, np.int64}:
                    val = str(int(data))
                elif type(data) in {np.float32, np.float64}:
                    val = "{:.5f}".format(data)
                else:
                    val = str(data)
                justname = name.ljust(max([len(key) for key in outkeys]))
                names.append(justname)
                datas.append(val)
        datas = dot_aligned(datas)
        outlist = [name + ' : ' + data for name, data in zip(names, datas)]
        outlist.sort()
        outstr = '\n'.join(outlist)
        mpi.message(outstr)

    def show(self):
        self.fig.show()

# Aliases
from .basic import Basic
from .thermo import Thermo
