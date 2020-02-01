from everest.builts._sliceable import Sliceable
from ..params import Params
from ..case import Case

class System(Sliceable):
    def __init__(
            self,
            **kwargs
            ):
        super().__init__(**kwargs)
        def sliceFn(params):
            return Case.build(system = self, params = params)
        self._slice_fns.append(sliceFn)
