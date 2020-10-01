import numpy as np

from everest.builts import Built
from everest.builts import Meta
from everest.builts._wanderer import Wanderer, LoadFail
from everest.value import Value
from everest.globevars import _GHOSTTAG_
from everest.builts import make_hash
from everest import wordhash
wHash = lambda x: wordhash.get_random_phrase(make_hash(x))
from everest.utilities import Grouper

from .. import fieldops
from ..utilities import hash_var
from ..observers import process_observers

from ..exceptions import PlanetEngineException, NotYetImplemented
from .. import observers as observersModule

class ObserverNotFound(PlanetEngineException):
    pass

class System(Wanderer):

    @classmethod
    def _process_inputs(cls, inputs):
        processed = dict()
        configs = {k: v for k, v in inputs.items() if k in cls.configsKeys}
        configs = cls._process_configs(configs)
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
    def _process_configs(cls, inputs):
        from .. import initials
        from ..traverse import Traverse
        if not type(inputs) is dict:
            if not type(inputs) in {list, tuple}:
                inputs = [inputs,]
            inputs = dict(zip(cls.configsKeys, inputs))
        configs = dict()
        for key, val in sorted(inputs.items()):
            if val is None:
                newVal = val
            elif type(val) is Meta:
                if issubclass(val, initials.Channel):
                    newVal = val()
                else:
                    raise TypeError
            elif isinstance(val, initials.Channel):
                newVal = val
            elif isinstance(val, System) or isinstance(val, Traverse):
                newVal = initials.Copy(val, key)
            elif type(val) is float:
                newVal = initials.Constant(val)
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

        self.chron = Value(float('NaN'))

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
        self.optionsHash = wHash(self.options)
        self.paramsHash = wHash(self.params)
        self.schemaHash = wHash(self.schema)
        self.caseHash = wHash(self.case)

        dOptions = self.options.copy()
        dOptions['hash'] = self.optionsHash
        dParams = self.params.copy()
        dParams['hash'] = self.paramsHash

        self.observers = []

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

        # Voyager attributes:
        self._changed_state_fns.append(self.prompt_observers)

        # Producer attributes:
        # self._post_save_fns.append(self.save_observers)

        # Built attributes:
        self._post_anchor_fns.insert(0, self.anchor_observers)

        # Local operations:
        if 'observers' in self.ghosts:
            self.add_observers(self.ghosts['observers'])

        self.configure(self.configs)

    def _voyager_outkeys(self):
        return ['chron', *sorted(self.configsKeys)]

    def _configure(self):
        self.c = Grouper(self.configs)

    def _initialise(self):
        if not hasattr(self, 'locals'):
            self.locals = Grouper(self.build_system(self.o, self.p, self.c))
            self.permutables.clear()
            self.permutables.update({
                key: getattr(self.locals, key) for key in self.configsKeys
                })
            self.observables = self.locals
            self.baselines.clear()
            self.baselines.update(
                {'mesh': fieldops.get_global_var_data(self.locals.mesh)}
                )
        for key, channel in sorted(self.configs.items()):
            if not channel is None:
                channel.apply(self.permutables[key])
        self.clipVals()
        self.setBounds()
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
        for varName, var in sorted(self.permutables.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_var(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(self.permutables.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

    def _voyager_out(self):
        yield self.chron.value
        for varName, var in sorted(self.permutables.items()):
            yield fieldops.get_global_var_data(var)

    def _load(self, loadDict):
        for key, loadData in sorted(loadDict.items()):
            if key == 'chron':
                self.chron.value = loadData
            else:
                var = getattr(self.locals, key)
                assert hasattr(var, 'mesh'), \
                    'Only meshVar supported at present.'
                nodes = var.mesh.data_nodegId
                for index, gId in enumerate(nodes):
                    var.data[index] = loadData[gId]
        self._update()

    def add_observer(self, observer):
        if not observer in self.observers:
            self.observers.append(observer)
            if self.anchored:
                observer.anchor(self.name, self.path)
            observer()

    def add_observers(self, inObservers):
        observers = process_observers(inObservers, self)
        for observer in observers:
            self.add_observer(observer)

    def add_default_observers(self):
        self.add_observers(*self.defaultObservers)

    @property
    def observer(self):
        if len(self.observers) == 0:
            raise ValueError("No observers added yet!")
        elif len(self.observers) == 1:
            return self.observers[0]
        else:
            raise ValueError("Multiple observers; specify one.")

    def remove_observer(self, toRemove):
        if type(toRemove) is int:
            self.observers.pop(toRemove)
        elif type(toRemove) is str:
            zipped = zip(
                [observer.hashID for observer in self.observers],
                self.observers
                )
            remIndex = None
            for index, (hashID, observer) in enumerate(zipped):
                if hashID == toRemove:
                    remIndex = index
            if remIndex is None: raise ObserverNotFound
            else: self.remove_observer(remIndex)
        else:
            self.observers.remove(toRemove)

    def prompt_observers(self):
        for observer in self.observers:
            observer()

    def save_observers(self):
        for observer in self.observers:
            observer.save()

    def anchor_observers(self):
        if not self.anchored:
            raise Exception
        for observer in self.observers:
            observer.anchor(self.name, self.path)

    def show(self):
        for observer in self.observers:
            try: observer.show()
            except NameError: pass

    def report(self):
        for observer in self.observers:
            try: observer.report()
            except NameError: pass

    defaultObservers = [observersModule.Thermo, observersModule.VelVisc]

    #
    # def __getitem__(self, arg):
    #     if type(arg) is tuple:
    #         raise NotYetImplemented
    #     elif type(arg) is slice:
    #         return self._system_get_slice(arg)
    #     else:
    #         out = self.__class__(**self.inputs)
    #         out.configure(arg)
    #         return out
    #
    # def _system_get_slice(self, indexer):
    #     from ..traverse import Traverse
    #     return Traverse(
    #         system = self,
    #         start = indexer.start,
    #         stop = indexer.stop,
    #         freq = indexer.step,
    #         observerClasses = []
    #         )

    # def _system_get_count(self, indexer):
    #     try:
    #         with self.bounce(indexer):
    #             return self.out()
    #     except LoadFail:
    #         nowCount = self.count.value
    #         self.store()
    #         self[:indexer]()
    #         out = self.out()
    #         self.load(nowCount)
    #         return out

# Aliases
from .conductive import Conductive
from .isovisc import Isovisc
from .arrhenius import Arrhenius
from .viscoplastic import Viscoplastic
from .viscoplasticmaterial import ViscoplasticMaterial
