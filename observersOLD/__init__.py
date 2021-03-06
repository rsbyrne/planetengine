import numpy as np

from everest.frames._counter import Counter
from everest.frames._cycler import Cycler
from everest.frames.condition import Condition
from everest.writer import LinkTo
from everest.globevars import _GHOSTTAG_

from planetengine.visualisation.quickfig import QuickFig

from ..utilities import _get_periodic_condition
from ..utilities import LightBoolean
from everest import mpi
from everest import disk

def process_observers(inObservers, system = None):
    observers = []
    if not type(inObservers) is list:
        inObservers = [inObservers,]
    for item in inObservers:
        freq = None
        observerInputs = dict()
        if type(item) is tuple:
            observer = item[0]
            if type(item[1]) is dict:
                observerInputs = item[1]
                if len(item) == 3:
                    freq = item[2]
            else:
                if len(item) > 2:
                    raise ValueError("Observer input invalid.")
                freq = item[1]
        else:
            observer = item
        if isinstance(observer, Observer):
            if system is None:
                raise Exception("No system provided to observe.")
            if not observer.observee is system:
                raise Exception("Mismatched observations.")
        elif issubclass(observer, Observer):
            if system is None:
                raise Exception("No system provided to observe.")
            observer = observer(system, **observerInputs)
        else:
            raise ValueError("Observer input invalid.")
        if not freq is None:
            observer.set_freqs(freq)
        observers.append(observer)
    return observers

class Observer(Counter, Cycler):

    @staticmethod
    def _process_inputs(inputs):
        processed = dict()
        processed.update(inputs)
        observee = processed['observee']
        if not observee.initialised:
            observee.initialise()
        if 'freq' in inputs:
            processed[_GHOSTTAG_ + 'freq'] = processed['freq']
            del processed['freq']
        return processed

    def __init__(self, **kwargs):

        # Expects:
        # self.observee
        # self.analysers
        # self.visVars

        super().__init__(
            observee = LinkTo(self.observee),
            supertype = 'Observer',
            **kwargs
            )

        self.fig = QuickFig(*self.visVars)

        # Producer attributes:
        self._outFns.append(self._out)
        self.analysers['chron'] = self.observee.chron
        self.outkeys.extend(sorted(self.analysers.keys()))

        # Cycler attributes:
        self._cycle_fns.append(self._observer_cycle)

        # Counter attributes:
        # self._count_update_fns.append(self.update)

        self.checkfreqs = dict()
        if 'freq' in self.ghosts:
            self.add_freqs(self.ghosts['freq'])

    @property
    def check(self):
        return any(self.checkfreqs.values())

    def set_freq(self, freq):
        self.checkfreqs.clear()
        self.add_freq(freq)
    def add_freq(self, freq):
        newfreq = _get_periodic_condition(self.observee, freq)
        freqID = disk.tempname()
        self.checkfreqs[freqID] = newfreq
        return freqID
    def add_freqs(self, freqs):
        if not type(freqs) is list:
            freqs = [freqs,]
        for freq in freqs:
            self.add_freq(freq)
    def remove_freq(self, freqID):
        del self.checkfreq[freqID]

    def update(self):
        if not self.observee.initialised:
            self.observee.initialise()
        self.count.value = self.observee.count.value

    def _observer_cycle(self):
        self.update()
        if self.check:
            self.store()

    def prompt(self):
        self()

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
        intTypes = {
            np.int8, np.int16, np.int32, np.int64,
            np.uint8, np.uint16, np.uint32, np.uint64
            }
        floatTypes = {np.float16, np.float32, np.float64}
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
                if type(data) in intTypes:
                    val = str(int(data))
                elif type(data) in floatTypes:
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
from .thermo import Thermo
from .velvisc import VelVisc
from .combo import Combo
