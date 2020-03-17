import time

from everest.builts import load, NotOnDiskError, NotInFrameError
from everest.builts._task import Task
from everest.builts.states import State
from everest.builts.condition import Condition
from everest.builts.states.threshold import Threshold
from everest.builts._iterator import LoadFail
from everest.builts._counter import Counter
# from everest.builts._diskbased import DiskBased
from everest.builts import check_global_anchor, _get_info, load, Meta, Built
from everest.weaklist import WeakList
from everest import mpi
from everest.globevars import _GHOSTTAG_

class Traverse(Task):

    _swapscript = '''from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        processed = dict()
        processed.update(inputs)
        end = inputs['stop']
        if not end is None and not isinstance(end, State):
            if type(end) is int: prop = 'count'
            elif type(end) is float: prop = 'chron'
            else: raise TypeError
            if end < 0.:
                system = inputs['system']
                if isinstance(system, Built):
                    end = end + getattr(system, prop).value
                else:
                    raise Exception(
                        "Relative end state only acceptable" \
                        + " when system provided."
                        )
            processed['stop'] = Threshold(
                prop = prop,
                op = 'ge',
                val = end
                )
        freq = inputs['freq']
        if not freq is None and not isinstance(freq, State):
            if type(freq) is int: prop = 'count'
            else: raise TypeError
            processed['freq'] = Threshold(
                prop = prop,
                op = 'mod',
                val = freq,
                inv = True
                )
        system = inputs['system']
        if type(system) is Meta:
            pass
        elif isinstance(system, Built):
            assert not len(inputs['vector'])
            processed['system'] = system.__class__
            processed['vector'] = system.inputs
            if inputs['start'] is None:
                if system.count.value in {-1, 0}:
                    initCount = 0
                else:
                    initCount = system.count.value
                processed['start'] = initCount
            processed[_GHOSTTAG_ + 'traversee'] = system
        return processed

    def __init__(self,
            system = None,
            vector = dict(),
            start = None,
            stop = None,
            freq = None,
            observerClasses = [],
            **kwargs
            ):

        self.system, self.start, self.stop, \
        self.freq, self.observerClasses, self.vector = \
                system, start, stop, \
                freq, observerClasses, vector
        self.observers = []

        ignoreme1, ignoreme2, self.vectorHash, ignoreme3, self.traverseeID = \
            _get_info(system, vector)

        super().__init__(**kwargs)

        # Task attributes:
        self._task_initialise_fns.append(self._traverse_initialise)
        self._task_cycler_fns.append(self._traverse_iterate)
        self._task_stop_fns.append(self._traverse_stop)
        self._task_finalise_fns.append(self._traverse_finalise)

    def _traverse_initialise(self):
        try:
            self.traversee = self.ghosts['traversee']
        except KeyError:
            try:
                self.traversee = load(
                    self.traverseeID,
                    self.name,
                    self.path
                    )
            except (NotOnDiskError, NotInFrameError):
                self.traversee = self.system(**self.vector)
        if self.anchored:
            self.traversee.anchor(self.name, self.path)
        if not self.start is None:
            try:
                self.traversee.load(self.start)
            except LoadFail:
                preTraverse = self.__class__(
                    system = self.traversee,
                    stop = self.start,
                    observerClasses = [],
                    )
                preTraverse()
        if self.freq is None and not self.stop is None:
            try:
                self.traversee.load(self.stop)
            except LoadFail:
                pass
        try:
            self.observers.extend(self.ghosts['observers'])
        except KeyError:
            pass
        for observerClass in self.observerClasses:
            observer = observerClass(self.traversee)
            self.observers.append(observer)
        for observer in self.observers:
            if self.anchored:
                observer.anchor(self.name, self.path)
            self.add_promptee(observer)
            observer.store()
        self.check = self._get_condition(self.traversee, self.freq)

    def _traverse_iterate(self):
        self.traversee()
        if self.check:
            self.traversee.store()

    def _traverse_stop(self):
        if self.stop is None: return False
        else: return self.stop(self.traversee)

    def _traverse_finalise(self):
        self.traversee.store()
        if self.traversee.anchored:
            self.traversee.save()
        for observer in self.observers:
            observer.store()
            if observer.anchored:
                observer.save()
            self.remove_promptee(observer)
        observers = [*self.observers]
        self.observers = []
        traversee = self.traversee
        del self.traversee
        if len(observers):
            return traversee, observers
        else:
            return traversee

    @staticmethod
    def _get_condition(traversee, freq):
        if isinstance(freq, Condition): return freq
        elif isinstance(freq, State): return Condition(freq, traversee)
        elif freq is None: return False
        else: assert False, ("Bad freq!", freq, type(freq))
