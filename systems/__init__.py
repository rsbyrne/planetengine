from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from everest.utilities import get_default_kwargs
from .. import case
from .. import params

class System(Sliceable, Callable):

    def __init__(
            self,
            **kwargs
            ):

        self.options = self.inputs
        self.defaultConfigs = self.defaults
        self.defaultParams = get_default_kwargs(self.buildFn)
        self.defaultOptions = get_default_kwargs(self.__init__)

        self.sliceDefaults = self.defaultParams

        super().__init__(**kwargs)

        from .._builttools import get_sliceFn
        sliceFn = get_sliceFn(self, params, case, ('system', 'params'))
        self._slice_fns.append(sliceFn)

        self._call_fns.append(self.parameterise)

    def parameterise(self, **inputs):
        modInps = {**self.defaultParams, **inputs}
        return self[params.build(**modInps)]

    @classmethod
    def make(cls, **inputs):
        modOptions, modParams, modConfigs, leftovers = {}, {}, {}, {}
        defaultConfigs = cls.defaults
        defaultParams = get_default_kwargs(cls.buildFn)
        defaultOptions = get_default_kwargs(cls.__init__)
        for key, val in sorted(inputs.items()):
            if key in defaultOptions: modOptions[key] = val
            elif key in defaultConfigs: modConfigs[key] = val
            elif key in defaultParams: modParams[key] = val
            else: leftovers[key] = val
        return cls.build(**modOptions)(**modParams)(**modConfigs)
