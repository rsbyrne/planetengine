import time

from everest.builts._task import Task
from everest.builts.states import State
from everest.builts.states.threshold import Threshold
from everest.builts._iterator import LoadFail
from everest.builts._counter import Counter
from everest.builts._diskbased import DiskBased
from everest.builts import check_global_anchor
from everest.builts import _get_info
from everest.weaklist import WeakList

from everest import mpi

class Traverse(Counter, Task, DiskBased):

    script = '''_script_from planetengine.traverse import Traverse as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        state = inputs['state']
        if not isinstance(state, State):
            if type(state) is int: prop = 'count'
            elif type(state) is float: prop = 'chron'
            else: raise TypeError
            inputs['state'] = Threshold(
                prop = prop,
                op = 'ge',
                val = state
                )

    def __init__(self,
            systemClass = None,
            state = None,
            observerClasses = [],
            express = True,
            **vector
            ):

        self.systemClass, self.state, self.express, \
                self.observerClasses, self.vector = \
                    systemClass, state, express, observerClasses, vector
        self.observers = []

        ignoreme1, self.vectorHash, ignoreme2, self.systemHashID = \
            _get_info(systemClass, vector)

        self.localObjects['traversee'] = self.systemHashID
        self.localObjects['vector'] = self.vectorHash

        super().__init__()

        # Task attributes:
        self._task_initialise_fns.append(self._traverse_initialise)
        self._task_cycler_fns.append(self._traverse_iterate)
        self._task_stop_fns.append(self._traverse_stop)
        self._task_finalise_fns.append(self._traverse_finalise)

    def _traverse_initialise(self):
        self.count.value = 0
        self.traversee = self.systemClass(**self.vector)
        if self.express:
            try:
                self.traversee.load(self.state)
            except LoadFail:
                if self.counts:
                    self.traversee.load(max(self.counts))
        self.count.value = self.traversee.count()
        self.traversee.store()
        self.traversee.save()
        self._last_checkpoint_time = mpi.share(time.time())
        for observerClass in self.observerClasses:
            observer = observerClass(self.traversee)
            self.observers.append(observer)
            self.add_promptee(observer)
            observer.store()

    def _traverse_iterate(self):
        self.traversee()
        self.count += 1
        time_now = mpi.share(time.time())
        time_since_last_checkpoint = time_now - self._last_checkpoint_time
        if time_since_last_checkpoint > 300.:
            self.traversee.store()
            self.store()
            self._last_checkpoint_time = time_now

    def _traverse_stop(self):
        return self.state(self.traversee)

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
