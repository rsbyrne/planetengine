from .. import fieldops
from .. import mapping
from .. import utilities
from ..systems import System
from ..traverse import Traverse
from everest.builts import load
from everest.globevars import _GHOSTTAG_
from . import IC

class Copy(IC):

    _swapscript = '''from planetengine.initials.copy import Copy as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        traverse = inputs['traverse']
        if isinstance(traverse, System):
            system = traverse
            traverse = system[:system.count()]
            # inputs[_GHOSTTAG_ + 'system'] = system
        elif not isinstance(traverse, Traverse): raise TypeError
        inputs['traverse'] = traverse

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
        loaded.load(self.traverse.endState)
        var = loaded.locals[self.varName]
        return fieldops.safe_box_evaluate(var, coordArray)
