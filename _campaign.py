import sys

from everest.builts.container import Container
from everest.builts._task import Task

from planetengine.traverse import Traverse

class CampaignIterable:
    def __init__(self, ):
        pass
    def __iter__(self):
        return self
    def __next__(self):
        return None

class Campaign(Container, Task):

    def __init__(self,
            vectors = None,
            observers = [],
            **kwargs
            ):

        self.observers = observers

        self._campaign_halt_toggle = False

        super().__init__(iterable = sampler, **kwargs)

        # Task attributes:
        self._task_initialise_fns.append(self.initialise)
        self._task_cycler_fns.append(self._campaign_cycle)
        self._task_stop_fns.append(self._campaign_halt)
        # self._task_finalise_fns.append()

    def _campaign_cycle(self):
        try:
            for ticket in self:
                traverse = ticket()
                for observer in self.observers:
                    traverse.add_promptee(observer)
                traverse()
                self.complete(ticket)
        except StopIteration:
            self._campaign_halt_toggle = True
        except:
            self.checkBack(ticket)
            exc_type, exc_val = sys.exc_info()[:2]
            output = exc_type(exc_val)
            raise output

    def _campaign_halt(self):
        if self._campaign_halt_toggle:
            self._campaign_halt_toggle = False
            return True
        else:
            return False
