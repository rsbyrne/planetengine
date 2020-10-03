import time

from everest.builts import load, NotOnDiskError
from everest.builts._task import Task
from everest.builts._boolean import Boolean
from everest.builts._voyager import LoadFail
from everest.builts import _get_info, load, Meta, Built # check_global_anchor,
from everest.weaklist import WeakList
from everest.globevars import _GHOSTTAG_
from everest.value import Value
from everest import mpi

from .utilities import LightBoolean, ChronCheck, _get_periodic_condition
from .finals import Final
from .observers import process_observers

def _process_negative_state(state, system):
    if state < 0:
        if not isinstance(system, Built):
            raise Exception(
                "Relative state only acceptable" \
                + " when system provided."
                )
        if type(state) is int:
            add = system.count.plain
        elif type(state) is float:
            add = system.chron.plain
        state = abs(state) + add
    return state

class Traverse(Task):

    _swapscript = '''from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        processed = dict()
        processed.update(inputs)
        start, stop, system = inputs['start'], inputs['stop'], inputs['system']
        systemConfigs = None
        # process start
        if type(start) is Value:
            start = start.plain
        if type(start) in {int, float}:
            start = _process_negative_state(start, system)
        elif type(start) is dict:
            self.systemConfigs = start
            start = 0
        elif start is None:
            if isinstance(system, Built):
                if system.count.plain in {-1, 0}:
                    start = 0
                else:
                    start = system.count.plain
            else:
                start = 0
        processed['start'] = start
        # process stop
        if type(stop) is Value:
            stop = stop.plain
        if type(stop) in {int, float}:
            stop = _process_negative_state(stop, system)
        elif isinstance(stop, Final):
            processed[_GHOSTTAG_ + 'stop'] = stop
            copyInps = stop.inputs.copy()
            ignoreme = copyInps.pop('system')
            stop = (stop.__class__, copyInps)
        processed['stop'] = stop
        # process system
        if type(system) is Meta:
            pass
        elif isinstance(system, Built):
            processed['system'] = system.__class__
            processed['vector'] = system.inputs
            if not systemConfigs is None:
                processed['vector'].update(systemConfigs)
            processed[_GHOSTTAG_ + 'traversee'] = system
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

        try:
            if start > stop:
                raise ValueError("Start index must be earlier than stop index.")
        except TypeError:
            pass

        self.system, self.freq, self.inObservers, self.vector = \
            system, freq, observers, vector
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
            except NotOnDiskError:
                self.traversee = self.system(**self.vector)
        if self.anchored:
            self.traversee.anchor(self.name, self.path)
        start, stop = self.inputs['start'], self.inputs['stop']
        try:
            stop = self.ghosts['stop']
        except KeyError:
            if type(stop) is tuple:
                stopClass, stopInputs = stop
                stop = stopClass(self.traversee, **stopInputs)
            else:
                try:
                    if issubclass(stop, Final):
                        stop = stop(self.traversee)
                except TypeError:
                    pass
        self.stop = stop
        if self.freq is None and not self.stop is None:
            try:
                # Skip straight to the end:
                self.traversee.load(self.stop)
            except LoadFail:
                # Go to the beginning:
                if start == 0:
                    self.traversee.initialise()
                else:
                    try:
                        self.traversee.load(start)
                    except LoadFail:
                        preTraverse = self.__class__(
                            system = self.traversee,
                            stop = start,
                            observers = [],
                            )
                        preTraverse()
        self.traversee.store()
        self.observers = process_observers(self.inObservers, self.traversee)
        self._observers_store()
        for observer in self.observers:
            if not observer in self.traversee.observers:
                self.add_promptee(observer)
            if self.anchored:
                observer.anchor(self.name, self.path)
                observer.save()
        self.check = _get_periodic_condition(self.traversee, self.freq)

    def _observers_store(self):
        for observer in self.traversee.observers:
            observer.store()
        for observer in self.observers:
            if not observer in self.traversee.observers:
                observer.store()

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
        self._observers_store()
        if self.traversee.anchored:
            self.traversee.save()
        for observer in self.observers:
            if not observer in self.traversee.observers:
                if self.anchored:
                    observer.save()
                self.remove_promptee(observer)
        observers = [
            o for o in self.observers if not o in self.traversee.observers
            ]
        self.observers = []
        traversee = self.traversee
        del self.traversee
        del self.stop
        if len(observers):
            return traversee, observers
        else:
            return traversee
