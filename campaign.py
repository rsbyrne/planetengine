import sys

from everest.builts.container import Container
from everest.builts._task import Task
from everest.builts._task import TaskSubrunFailed
from everest.vectorset import VectorSet

from .traverse import Traverse

class CampaignIterable:
    def __init__(self, systemClass, state, observerClasses, **vectorSets):
        self.systemClass, self.state, self.observerClasses = \
            systemClass, state, observerClasses
        self.vectorSets = vectorSets
    def __iter__(self):
        self.vectors = iter(VectorSet(**self.vectorSets))
        return self
    def __next__(self):
        vector = next(self.vectors)
        out = Traverse(
            self.systemClass,
            self.state,
            self.observerClasses,
            express = True,
            **vector
            )
        return out

class Campaign(Container, Task):

    script = '''_script_from planetengine.campaign import Campaign as CLASS'''

    def __init__(self,
            systemClass = None,
            state = None,
            observerClasses = [],
            cores = 1,
            **vectorSets
            ):

        self.cores = cores

        iterable = CampaignIterable(
            systemClass,
            state,
            observerClasses,
            **vectorSets
            )

        self._campaign_halt_toggle = False
        self._held_ticket = None

        super().__init__(iterable = iterable)

        # Task attributes:
        self._task_initialise_fns.append(self.initialise)
        self._task_cycler_fns.append(self._campaign_cycle)
        self._task_stop_fns.append(self._campaign_halt)
        # self._task_finalise_fns.append()

    def _campaign_cycle(self):
        try:
            for ticket in self:
                self._held_ticket = ticket
                traverse = ticket()
                try:
                    traverse.subrun(self.cores)
                    self.complete(ticket)
                except TaskSubrunFailed as e:
                    self.checkFail(ticket, e)
                self._held_ticket = None
            else:
                self._campaign_halt_toggle = True
        except:
            if not self._held_ticket is None:
                self.checkBack(self._held_ticket)
            exc_type, exc_val = sys.exc_info()[:2]
            output = exc_type(exc_val)
            raise output

    def _campaign_halt(self):
        if self._campaign_halt_toggle:
            self._campaign_halt_toggle = False
            return True
        else:
            return False
