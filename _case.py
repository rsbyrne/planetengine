from everest.builts._sliceable import Sliceable
from .configs import Configs
from .real import Real
from .utilities import Grouper

class Case(Sliceable):
    from .case import __file__ as _file_
    def __init__(
            self,
            system = None,
            params = None,
            **kwargs
            ):
        localsDict = system.parameterise(**params.inputs)
        self.system = system
        self.params = params
        self.locals = Grouper(localsDict)
        self.varsOfState = self.locals.varsOfState
        super().__init__(**kwargs)
        def configs_sliceFn(configs):
            return Real.build(case = self, configs = configs)
        self._slice_fns.append(configs_sliceFn)
