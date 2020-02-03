from everest.builts._sliceable import Sliceable
from .. import case

class System(Sliceable):
    def __init__(
            self,
            **kwargs
            ):
        super().__init__(**kwargs)
        def sliceFn(params):
            return case.build(system = self, params = params)
        self._slice_fns.append(sliceFn)
