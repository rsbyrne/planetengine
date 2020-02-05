from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from . import case
from . import params as paramsMod

class Optionalisation(Sliceable, Callable):

    from .case import __file__ as _file_

    def __init__(
            self,
            system = None,
            options = None,
            **kwargs
            ):

        self.system = system
        self.options = options
        super().__init__(**kwargs)
        self._slice_fns.append(self.slice)
        self._call_fns.append(self.parameterise)

    def parameterise(self, **inputs):
        return self.slice(paramsMod.build(**inputs))

    def slice(self, arg):
        return case.build(optionalisation = self, params = arg)
