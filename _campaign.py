import sys

from everest.builts.container import Container
from everest.builts._task import Task
from everest.vectorset import VectorSet

from planetengine.traverse import Traverse

class CampaignIterable:
    def __init__(self, system, state, **vectorSets):
        self.vectorSets = vectorSets
        self.system, self.state = system, state
    def __iter__(self):
        self.vectors = iter(VectorSet(**self.vectorSets))
        return self
    def __next__(self):
        vector = next(self.vectors)
        return Traverse(self.system, vector, self.state)

class Campaign(Container, Task):

    def __init__(self,
            system = None,
            state = None,
            observers = [],
            **vectorSets
            ):

        self.observers = observers

        iterable = CampaignIterable(system, state, **vectorSets)

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
                for observer in self.observers:
                    traverse.add_promptee(observer)
                traverse()
                self.complete(ticket)
                self._held_ticket = None
            else:
                self._campaign_halt_toggle = True
        except StopIteration:
            self._campaign_halt_toggle = True
        except:
            self.checkBack(self._held_ticket)
            self._held_ticket = None
            exc_type, exc_val = sys.exc_info()[:2]
            output = exc_type(exc_val)
            raise output

    def _campaign_halt(self):
        if self._campaign_halt_toggle:
            self._campaign_halt_toggle = False
            return True
        else:
            return False
