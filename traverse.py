import time

from everest.builts._task import Task
from everest.builts.states import State
from everest.builts.condition import Condition
from everest.builts.states.threshold import Threshold
from everest.builts._iterator import LoadFail
from everest.builts._counter import Counter
from everest.builts._diskbased import DiskBased
from everest.builts import check_global_anchor, _get_info, load, Meta, Built
from everest.weaklist import WeakList
from everest import mpi
from everest.globevars import _GHOSTTAG_

class Traverse(Counter, Task, DiskBased):

    _swapscript = '''from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        state = inputs['endState']
        if not state is None and not isinstance(state, State):
            if type(state) is int: prop = 'count'
            elif type(state) is float: prop = 'chron'
            else: raise TypeError
            inputs['endState'] = Threshold(
                prop = prop,
                op = 'ge',
                val = state
                )
        freq = inputs['freq']
        if not freq is None and not isinstance(freq, State):
            if type(freq) is int: prop = 'count'
            else: raise TypeError
            inputs['freq'] = Threshold(
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
            inputs['system'] = system.__class__
            inputs['vector'] = system.inputs
            if inputs['initState'] is None:
                inputs['initState'] = system.count.value
            inputs[_GHOSTTAG_ + 'traversee'] = system

    def __init__(self,
            system = None,
            vector = dict(),
            initState = None,
            endState = None,
            freq = None,
            observerClasses = [],
            **kwargs
            ):

        self.system, self.initState, self.endState, \
        self.freq, self.observerClasses, self.vector = \
                system, initState, endState, \
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

        self.set_checkpoint_interval(300)

    def set_checkpoint_interval(self, interval):
        self.checkpointInterval = interval

    def _traverse_initialise(self):
        self.count.value = 0
        try: self.traversee = self.ghosts['traversee']
        except KeyError: self.traversee = self.system(**self.vector)
        if not self.initState is None:
            try:
                self.traversee.load(self.initState)
            except LoadFail:
                preTraverse = self.__class__(
                    system = self.traversee,
                    endState = self.initState,
                    observerClasses = [],
                    )
                preTraverse()
                self.traversee.load(self.initState)
        if self.freq is None and not self.endState is None:
            try:
                self.traversee.load(self.endState)
            except LoadFail:
                pass
        self.count.value = self.traversee.count()
        self.traversee.store()
        self.traversee.save()
        self._last_checkpoint_time = mpi.share(time.time())
        for observerClass in self.observerClasses:
            observer = observerClass(self.traversee)
            self.observers.append(observer)
            self.add_promptee(observer)
            observer.store()
        self.check = self._get_condition(self.traversee, self.freq)

    def _traverse_iterate(self):
        self.traversee()
        self.count += 1
        time_now = mpi.share(time.time())
        time_since_last_checkpoint = time_now - self._last_checkpoint_time
        if self.check:
            self.traversee.store()
            self.store()
        if time_since_last_checkpoint > self.checkpointInterval:
            if not self.check:
                self.traversee.store()
                self.store()
            self.traversee.save()
            for observer in self.observers:
                observer.save()
            self.save()
            self._last_checkpoint_time = time_now

    def _traverse_stop(self):
        if self.endState is None:
            return False
        else:
            return self.endState(self.traversee)

    def _traverse_finalise(self):
        self.traversee.store()
        self.traversee.save()
        self.store()
        self.save()
        del self.traversee
        for observer in self.observers:
            observer.store()
            observer.save()
            self.remove_promptee(observer)
        self.observers = []

    @staticmethod
    def _get_condition(traversee, freq):
        if isinstance(freq, Condition): return freq
        elif isinstance(freq, State): return Condition(freq, traversee)
        elif freq is None: return False
        else: assert False, ("Bad freq!", freq, type(freq))
