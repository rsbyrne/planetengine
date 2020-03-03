from .. import fieldops
from .. import mapping
from .. import utilities
from ..systems import System
from ..traverse import Traverse
from everest.builts import load
from . import IC

class Copy(IC):

    _swapscript = '''from planetengine.initials.copy import Copy as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        traverse = inputs['traverse']
        if isinstance(traverse, Traverse):
            pass
        elif isinstance(traverse, System):
            traverse = Traverse(
                traverse.__class__,
                traverse.inputs,
                traverse.count(),
                express = True
                )
            inputs['traverse'] = traverse
        else:
            raise TypeError

    def __init__(self,
            traverse,
            varName,
            **kwargs
            ):

        self.traverse, self.varName = traverse, varName

        super().__init__(**kwargs)

    def evaluate(self, coordArray):
        self.traverse()
        loaded = load(self.traverse.traverseeID)
        loaded.load(self.traverse.state)
        var = loaded.locals[self.varName]
        return fieldops.safe_box_evaluate(var, coordArray)