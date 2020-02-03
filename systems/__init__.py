from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from .. import case
from .. import params

class System(Sliceable, Callable):

    def __init__(
            self,
            make,
            **kwargs
            ):

        self.make = make

        super().__init__(**kwargs)

        def sliceFn(inParams):
            return case.build(system = self, params = inParams)
        self._slice_fns.append(sliceFn)

        self._call_fns.append(self.parameterise)

    def parameterise(self, **inputs):
        return self[params.build(**inputs)]
