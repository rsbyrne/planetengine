from .. import fieldops
from .. import mapping
from .. import utilities
from ..systems import System
from ..traverse import Traverse
from everest.builts._task import Task
from everest.builts import load
from . import IC

class Copy(IC):

    _swapscript = '''from planetengine.initials.copy import Copy as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        task = inputs['task']
        if isinstance(task, Task):
            pass
        elif isinstance(task, System):
            task = Traverse(
                task.__class__,
                task.inputs,
                task.count(),
                express = True
                )
            inputs['task'] = task
        else:
            raise TypeError

    def __init__(self,
            task,
            varName,
            **kwargs
            ):

        self.task, self.varName = task, varName

        super().__init__(**kwargs)

    def evaluate(self, coordArray):
        loaded = self.task.get_final()
        var = loaded.locals[self.varName]
        return fieldops.safe_box_evaluate(var, coordArray)
