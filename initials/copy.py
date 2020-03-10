from .. import fieldops
from .. import mapping
from .. import utilities
from ..systems import System
from ..traverse import Traverse
from everest.builts import load
from everest.globevars import _GHOSTTAG_
from . import Channel

class Copy(Channel):

    _swapscript = '''from planetengine.initials.copy import Copy as CLASS'''

    @staticmethod
    def _process_inputs(inputs):
        traverse = inputs['traverse']
        if isinstance(traverse, System):
            traversee = traverse
            traverse = traversee[:system.count()]
        elif isinstance(traverse, Traverse):
            try:
                traversee = traverse.ghosts['traversee']
            except KeyError:
                traversee = traverse.system(traverse.vector)
        else:
            raise TypeError
        inputs[_GHOSTTAG_ + 'traversee'] = traversee
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
        traversee = self.ghosts['traversee']
        loaded = load(self.traverse.traverseeID)
        loaded.load(self.traverse.endState)
        var = loaded.locals[self.varName]
        return fieldops.safe_box_evaluate(var, coordArray)
