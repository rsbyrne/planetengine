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

from .utilities import LightBoolean

class ChronCheck:
    def __init__(self, value, interval):
        self.interval = interval
        self.value = value
        self.previous = None
    def __bool__(self):
        if self.previous is None:
            self.previous = self.value.value
            return True
        else:
            target = self.previous + self.interval
            if self.value >= self.previous + self.interval:
                self.previous = target
                return True
            else:
                return False

class Traverse(Task):

    _swapscript = '''from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        processed = dict()
        processed.update(inputs)
        stop = inputs['stop']
        system = inputs['system']
        if type(stop) in {int, float}:
            if stop < 0:
                if not isinstance(system, Built):
                    raise Exception(
                        "Relative end state only acceptable" \
                        + " when system provided."
                        )
                if type(stop) is int:
                    add = system.count.value
                elif type(stop) is float:
                    add = system.count.value
                else:
                    raise TypeError("Stop arg not recognised.")
                stop = abs(stop) + add
                processed['stop'] = stop
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
        if self.stop is None:
            return False
        elif type(self.stop) is int:
            return self.traversee.count >= self.stop
        elif type(self.stop) is float:
            return self.traversee.chron >= self.stop
        elif isinstance(self.stop, Condition):
            return bool(self.stop)
        elif isinstance(self.stop, State):
            return self.stop(self.traversee)
        else:
            assert False, "Invalid stop argument."

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
        if isinstance(freq, Condition):
            return freq
        elif isinstance(freq, State):
            return Condition(freq, traversee)
        elif freq is None:
            return False
        elif type(freq) is int:
            return LightBoolean(lambda: not traversee.count % freq)
        elif type(freq) is float:
            return ChronCheck(traversee.chron, freq)
        else: assert False, ("Bad freq!", freq, type(freq))
