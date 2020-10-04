import numpy as np

from everest.builts import Built, w_hash
from everest.builts import Meta
from everest.builts._wanderer import Wanderer
from everest.builts._chroner import Chroner
from everest.value import Value
from everest.globevars import _GHOSTTAG_
from everest.utilities import Grouper, make_hash

from .. import fieldops
from ..utilities import hash_var
from ..observers import process_observers

from ..exceptions import PlanetEngineException, NotYetImplemented
from .. import observers as observersModule

class ObserverNotFound(PlanetEngineException):
    pass

class Mutable:
    def __init__(self, var):
        self.var = var
    def __setitem__(self, arg1, arg2):
        if not arg1 is Ellipsis:
            raise TypeError
        arg2.apply(arg1)

class System(Chroner, Wanderer):

    @classmethod
    def _process_inputs(cls, inputs):
        processed = dict()
        configs = {k: v for k, v in inputs.items() if k in cls.configsKeys}
        configs = cls._process_configs(**configs)
        for key, val in sorted(inputs.items()):
            if key in cls.configsKeys:
                processed[_GHOSTTAG_ + key] = configs[key]
            else:
                processed[key] = val
        if 'observers' in inputs:
            processed[_GHOSTTAG_ + 'observers'] = processed['observers']
            del processed['observers']
        if 'initialise' in inputs:
            del processed['initialise']
            processed[_GHOSTTAG_ + 'initialise'] = inputs['initialise']
        return processed

    @classmethod
    def _process_configs(cls, **inputs):
        from .. import initials
        from ..traverse import Traverse
        if not type(inputs) is dict:
            if not type(inputs) in {list, tuple}:
                inputs = [inputs,]
            inputs = dict(zip(cls.configsKeys, inputs))
        configs = dict()
        for key, val in sorted(inputs.items()):
            if val is None:
                raise ValueError
            elif type(val) is Meta:
                if issubclass(val, initials.Channel):
                    newVal = val()
                else:
                    raise TypeError
            elif isinstance(val, initials.Channel):
                newVal = val
            elif isinstance(val, System) or isinstance(val, Traverse):
                newVal = initials.Copy(val, key)
            elif type(val) in {int, float}:
                newVal = val
            else:
                raise TypeError(type(val))
            configs[key] = newVal
        for key in cls.configsKeys:
            if not key in configs:
                configs[key] = cls.defaultInps[key]
        return configs

    @classmethod
    def _custom_cls_fn(cls):
        for key in {'options', 'params', 'configs'}:
            if key in cls._sortedInputKeys:
                inputKeys = cls._sortedInputKeys[key]
                setattr(cls, key + 'Keys', inputKeys)
                setattr(cls, 'default' + key.capitalize(), {
                    key: val \
                        for key, val in sorted(cls.defaultInps.items()) \
                            if key in inputKeys
                    })

    @classmethod
    def _sort_inputs(cls, inputs, ghosts):
        optionsDict = {**cls.defaultOptions}
        paramsDict = {**cls.defaultParams}
        configsDict = {**cls.defaultConfigs}
        leftoversDict = {}
        for key, val in [*sorted(inputs.items()), *sorted(ghosts.items())]:
            if key in cls.defaultOptions:
                optionsDict[key] = val
            elif key in cls.defaultParams:
                paramsDict[key] = val
            elif key in cls.defaultConfigs:
                configsDict[key] = val
            else:
                leftoversDict[key] = val
        return optionsDict, paramsDict, configsDict, leftoversDict

    def __init__(self, **kwargs):

        # Voyager expects:
        # self._initialise
        # self._iterate
        # self._out
        # self._outkeys
        # self._load

        self.options, self.params, self.configs, self.leftovers = \
            self._sort_inputs(self.inputs, self.ghosts)
        self.o, self.p, self.c = \
            Grouper(self.options), Grouper(self.params), Grouper(self.configs)
        self.schema = self.__class__
        self.case = (self.schema, self.params)
#         self.prevConfigs = dict()

        self.schemaHash = make_hash(self.schema)
        self.optionsHash = w_hash(self.options)
        self.paramsHash = w_hash(self.params)
        self.schemaHash = w_hash(self.schema)
        self.caseHash = w_hash(self.case)

        dOptions = self.options.copy()
        dOptions['hash'] = self.optionsHash
        dParams = self.params.copy()
        dParams['hash'] = self.paramsHash

        # self.observers = []

        if 'initialise' in self.ghosts:
            initialise = self.ghosts['initialise']
        else:
            initialise = False

        super().__init__(
            options = dOptions,
            params = dParams,
            schema = self.typeHash,
            case = self.caseHash,
            _voyager_initialise = initialise,
            supertype = 'System',
            **kwargs
            )

        # Wanderer attributes:
        self._wanderer_configure_post_fns.append(
            self._system_configure_post_fn
            )
        self.configure(**{k: self.ghosts[k] for k in self.configsKeys})

        # Voyager attributes:
        # self._changed_state_fns.append(self.prompt_observers)

        # Producer attributes:
        # self._post_save_fns.append(self.save_observers)

        # Built attributes:
        # self._post_anchor_fns.insert(0, self.anchor_observers)

        # Local operations:
        # if 'observers' in self.ghosts:
        #     self.add_observers(self.ghosts['observers'])

    def _system_configure_post_fn(self):
        self.c = Grouper(self.configs)
        if self.initialised:
            self.clipVals()
            self.setBounds()

    def _initialise(self):
        if not hasattr(self, 'locals'):
            self.locals = Grouper(self.build_system(self.o, self.p, self.c))
            del self.locals.self
            self.mutables.clear()
            self.mutables.update({
                key: self.locals[key] for key in self.configsKeys
                })
            self.observables.clear()
            self.observables.update(self.locals)
            self.baselines.clear()
            self.baselines.update(
                {'mesh': fieldops.get_global_var_data(self.locals.mesh)}
                )
        self._configure()
        self.chron.value = 0.
        self._update()

    def _iterate(self):
        dt = self._integrate(_skipClips = True)
        self._update()
        self.chron += dt

    def _integrate(self, _skipClips = False):
        dt = self.locals.integrate()
        if not _skipClips:
            self.clipVals()
            self.setBounds()
        return dt

    def _update(self):
        self.locals.update()

    def clipVals(self):
        for varName, var in sorted(self.mutables.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_var(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(self.mutables.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

    def _voyager_outkeys(self):
        for o in self.configsKeys: yield o
    def _voyager_out(self):
        for varName, var in sorted(self.mutables.items()):
            yield fieldops.get_global_var_data(var)

    def _voyager_load_update(self, loadDict):
        for key, loadData in sorted(loadDict.items()):
            var = getattr(self.locals, key)
            assert hasattr(var, 'mesh'), \
                'Only meshVar supported at present.'
            nodes = var.mesh.data_nodegId
            for index, gId in enumerate(nodes):
                var.data[index] = loadData[gId]
        self._update()

# Aliases
from .conductive import Conductive
from .isovisc import Isovisc
from .arrhenius import Arrhenius
from .viscoplastic import Viscoplastic
from .viscoplasticmaterial import ViscoplasticMaterial
