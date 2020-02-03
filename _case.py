from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from . import real
from . import configs
from .utilities import Grouper

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

        def sliceFn(inConfigs):
            return real.build(case = self, configs = inConfigs)
        self._slice_fns.append(sliceFn)

        self._call_fns.append(self.configure)

    def configure(self, **inputs):
        modInps = {**self.system.defaultConfigs, **inputs}
        return self[configs.build(**modInps)]
