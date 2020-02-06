from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from . import real
from . import configs as configsMod

class Case(Sliceable, Callable):

    from .case import __file__ as _file_

    def __init__(
            self,
            optionalisation = None,
            params = None,
            **kwargs
            ):

        self.optionalisation = optionalisation
        self.params = params
        super().__init__(**kwargs)
        self._slice_fns.append(self.slice)
        self._call_fns.append(self.configure)

    def configure(self, **inputs):
        return self.slice(configsMod.build(**inputs))

    def slice(self, arg):
        return real.build(case = self, configs = arg)
