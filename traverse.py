import time

from everest.builts import load, NotOnDiskError, NotInFrameError
from everest.builts._task import Task
from everest.builts._boolean import Boolean
from everest.builts._iterator import LoadFail
from everest.builts import check_global_anchor, _get_info, load, Meta, Built
from everest.weaklist import WeakList
from everest.globevars import _GHOSTTAG_
from everest.value import Value
from everest import mpi

from .utilities import LightBoolean, ChronCheck, _get_periodic_condition

class Traverse(Task):

    _swapscript = '''from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        processed = dict()
        processed.update(inputs)
        start, stop = inputs['start'], inputs['stop']
        system = inputs['system']
        for name, indexer in sorted({'start': start, 'stop': stop}.items()):
            if type(indexer) is Value:
                indexer = indexer.plain
            if type(indexer) in {int, float}:
                if indexer < 0:
                    if not isinstance(system, Built):
                        raise Exception(
                            "Relative end state only acceptable" \
                            + " when system provided."
                            )
                    if type(indexer) is int:
                        add = system.count.plain
                    elif type(indexer) is float:
                        add = system.chron.plain
                    else:
                        raise TypeError("Stop arg not recognised.")
                    indexer = abs(indexer) + add
            processed[name] = indexer
        if type(system) is Meta:
            pass
        elif isinstance(system, Built):
            # assert not len(inputs['vector']), inputs['vector']
            processed['system'] = system.__class__
            processed['vector'] = system.inputs
            if inputs['start'] is None:
                if system.count.plain in {-1, 0}:
                    initCount = 0
                else:
                    initCount = system.count.plain
                processed['start'] = initCount
            processed[_GHOSTTAG_ + 'traversee'] = system
        # assert not type(processed['stop']) is Value
        return processed

    def __init__(self,
            system = None,
            vector = dict(),
            start = None,
            stop = None,
            freq = None,
            observers = [],
            **kwargs
            ):

        self.system, self.start, self.stop, \
        self.freq, self.inObservers, self.vector = \
                system, start, stop, \
                freq, observers, vector
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
        if self.freq is None and not self.stop is None:
            try:
                # Skip straight to the end:
                self.traversee.load(self.stop)
            except LoadFail:
                # Go to the beginning:
                if self.start == 0:
                    self.traversee.initialise()
                else:
                    try:
                        self.traversee.load(self.start)
                    except LoadFail:
                        preTraverse = self.__class__(
                            system = self.traversee,
                            stop = self.start,
                            observers = [],
                            )
                        preTraverse()
        self.traversee.store()
        self.observers = self._get_observers(self.traversee, self.inObservers)
        for observer in self.observers:
            if self.anchored:
                observer.anchor(self.name, self.path)
            self.add_promptee(observer)
            observer.store()
        self.check = _get_periodic_condition(self.traversee, self.freq)

    @staticmethod
    def _get_observers(traversee, inObservers):
        from planetengine.observers import Observer
        observers = []
        for item in inObservers:
            if type(item) is tuple:
                if not len(item) == 3:
                    raise Exception("Inappropriate observer input.")
                observerClass, observerInputs, observerFreq = item
                observer = observerClass(traversee, **observerInputs)
                observer.set_freq(observerFreq)
            if isinstance(item, Observer):
                if not item.observee is traversee:
                    raise Exception("Mismatched observations.")
                observer = item
            elif issubclass(item, Observer):
                observerClass = item
                observer = observerClass(traversee)
            observers.append(observer)
        for observer in traversee.observers:
            if not observer in observers:
                observers.append(observer)
        return observers

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
        elif isinstance(self.stop, Boolean):
            return bool(self.stop)
        else:
            assert False, ("Invalid stop argument.", self.stop, type(self.stop))

    def _traverse_finalise(self):
        self.traversee.store()
        if self.traversee.anchored:
            self.traversee.save()
        for observer in self.observers:
            observer.store()
            if observer.anchored:
                observer.save()
            self.remove_promptee(observer)
        observers = [
            o for o in self.observers if not o in self.traversee.observers
            ]
        self.observers = []
        traversee = self.traversee
        del self.traversee
        if len(observers):
            return traversee, observers
        else:
            return traversee
