from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from . import real
from . import configs
from .utilities import Grouper
from ._builttools import yield_sliceFn

class Case(Sliceable, Callable):

    from .case import __file__ as _file_

    def __init__(
            self,
            system = None,
            params = None,
            **kwargs
            ):

        localsDict = system.buildFn(**params.inputs)
        self.locals = Grouper(localsDict)

        self.system = system
        self.params = params
        self.varsOfState = self.locals.varsOfState

        super().__init__(**kwargs)

        from ._builttools import get_sliceFn
        sliceFn = get_sliceFn(self, configs, real, ('case', 'configs'))
        self._slice_fns.append(sliceFn)

        self._call_fns.append(self.configure)

    def configure(self, **inputs):
        modInps = {**self.system.defaultConfigs, **inputs}
        return self[configs.build(**modInps)]