from everest.builts._sliceable import Sliceable
from everest.builts._callable import Callable
from everest.utilities import get_default_kwargs
from .. import optionalisation
from .. import options as optionsMod
from .. import params as paramsMod
from .. import configs as configsMod

class System(Sliceable, Callable):

    def __init__(
            self,
            optionKeys = {},
            paramKeys = {},
            configsKeys = {},
            varsOfStateKeys = {},
            obsVarsKeys = {},
            buildFn = None,
            **kwargs
            ):

        defaults = get_default_kwargs(buildFn)
        defaultOptions = {
            key: val for key, val in sorted(defaults.items()) if key in optionKeys
            }
        defaultParams = {
            key: val for key, val in sorted(defaults.items()) if key in paramKeys
            }
        defaultConfigs = {
            key: val for key, val in sorted(defaults.items()) if key in configsKeys
            }
        self.optionKeys, self.paramKeys, self.configsKeys = \
            optionKeys, paramKeys, configsKeys
        self.varsOfStateKeys, self.obsVarsKeys = \
            varsOfStateKeys, obsVarsKeys
        self.buildFn = \
            buildFn
        self.defaultOptions, self.defaultParams, self.defaultConfigs = \
            defaultOptions, defaultParams, defaultConfigs
        super().__init__(**kwargs)
        self._slice_fns.append(self.slice)
        self._call_fns.append(self.optionalise)

    def optionalise(self, **inputs):
        return self.slice(optionsMod.build(**inputs))

    def slice(self, arg):
        return optionalisation.build(system = self, options = arg)

    @classmethod
    def make(cls, **inputs):
        initDict = {}
        for key, val in sorted(inputs.items()):
            if key in system.defaultInps:
                initDict[key] = val
        system = cls.build(**initDict)
        optionsDict = {}
        paramsDict = {}
        configsDict = {}
        leftoversDict = {}
        for key, val in sorted(inputs.items()):
            if key in system.defaultOptions:
                optionsDict[key] = val
            elif key in system.defaultParams:
                paramsDict[key] = val
            elif key in system.defaultConfigs:
                configsDict[key] = val
            else:
                leftoversDict[key] = val
        return system(**optionsDict)(**paramsDict)(**configsDict)
