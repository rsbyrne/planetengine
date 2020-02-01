from everest.builts._sliceable import Sliceable
from planetengine.configs import Configs
from planetengine.real import Real
from planetengine.utilities import Grouper

class Case(Sliceable):
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

CLASS = Case
build, get = CLASS.build, CLASS.get
