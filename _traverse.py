import time

from everest.builts._task import Task
from everest.builts.states import State
from everest.builts.states.threshold import Threshold
from everest.builts._iterator import LoadFail
from everest.builts._counter import Counter
from everest.builts import check_global_anchor
from everest.builts import _get_info

from everest import mpi

class Traverse(Counter, Task):

    global _file_

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
            cosmos = None,
            state = None,
            express = True,
            **vector
            ):

        check_global_anchor()

        self.cosmos, self.state, self.express, self.vector = \
            cosmos, state, express, vector

        ignoreme1, self.vectorHash, ignoreme2, self.systemHashID = \
            _get_info(cosmos, vector)

        self.localObjects['traversee'] = self.systemHashID
        self.localObjects['vector'] = self.vectorHash

        super().__init__(_iterator_initialise = False)

        # Task attributes:
        self._task_initialise_fns.append(self._traverse_initialise)
        self._task_cycler_fns.append(self._traverse_iterate)
        self._task_stop_fns.append(self._traverse_stop)
        self._task_finalise_fns.append(self._traverse_finalise)

    def _traverse_initialise(self):
        self.count.value = 0
        self.traversee = self.cosmos(**self.vector)
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

    def _traverse_iterate(self):
        self.traversee()
        self.count += 1
        time_now = mpi.share(time.time())
        time_since_last_checkpoint = time_now - self._last_checkpoint_time
        if time_since_last_checkpoint > 600.:
            self.traversee.store()
            self.store()
            time_since_last_checkpoint = time_now

    def _traverse_stop(self):
        return self.state(self.traversee)

    def _traverse_finalise(self):
        self.traversee.store()
        self.traversee.save()
        self.store()
        self.save()
        del self.traversee

from . import traverse as module
_file_ = module.__file__
