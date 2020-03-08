import numpy as np

from everest.builts import Built
from everest.builts._iterator import Iterator, LoadFail
from everest.value import Value
from everest.builts.vector import Vector
from everest.writer import FixedDataset
from everest.builts import make_hash

from .. import fieldops
from ..utilities import hash_var
from ..utilities import Grouper

def _make_locals(localsDict):
    del localsDict['self']
    return Grouper(localsDict)

class System(Iterator):

    @classmethod
    def _process_inputs(cls, inputs):
        for key, val in sorted(inputs.items()):
            if key in cls.configsKeys:
                if type(val) is cls:
                    from ..initials.copy import Copy
                    inputs[key] = Copy(val, key)

    @classmethod
    def _make_defaults(cls, keys):
        outDict = {
            key: val \
                for key, val in sorted(cls.defaultInps.items()) \
                    if key in keys
            }
        return outDict

    @classmethod
    def _custom_cls_fn(cls):
        if hasattr(cls, 'optionsKeys'):
            cls.defaultOptions = cls._make_defaults(cls.optionsKeys)
            cls.defaultParams = cls._make_defaults(cls.paramsKeys)
            cls.defaultConfigs = cls._make_defaults(cls.configsKeys)

    @classmethod
    def _sort_inputs(cls, inputs):
        optionsDict = {**cls.defaultOptions}
        paramsDict = {**cls.defaultParams}
        configsDict = {**cls.defaultConfigs}
        leftoversDict = {}
        for key, val in sorted(inputs.items()):
            if key in cls.defaultOptions:
                optionsDict[key] = val
            elif key in cls.defaultParams:
                paramsDict[key] = val
            elif key in cls.defaultConfigs:
                configsDict[key] = val
            else:
                leftoversDict[key] = val
        return optionsDict, paramsDict, configsDict, leftoversDict

    @classmethod
    def vectorise(cls, vector):
        if isinstance(vector, Vector):
            inputs = vector.inputs
        elif type(vector) is dict:
            inputs = vector
        return cls(**inputs)

    def __init__(self, localsDict, **kwargs):

        # Expects:
        # self.locals
        # self.locals.update
        # self.locals.integrate

        self.locals = _make_locals(localsDict)

        self.options, self.params, self.configs, self.leftovers = \
            self._sort_inputs(self.inputs)
        self.chron = Value(0.)
        self.varsOfState = {
            key: self.locals[key] for key in self.configsKeys
            }

        self._outkeys = ['chron', *sorted(self.varsOfState.keys())]

        # Iterator expects:
        # self._initialise
        # self._iterate
        # self._out
        # self._outkeys
        # self._load

        self.baselines = {
            'mesh': FixedDataset(
                fieldops.get_global_var_data(self.locals.mesh)
                )
            }
        dOptions, dParams, dConfigs = \
            self.options.copy(), self.params.copy(), self.configs.copy()
        dOptions['hash'] = make_hash(self.options)
        dParams['hash'] = make_hash(self.params)
        dConfigs['hash'] = make_hash(self.configs)

        super().__init__(
            baselines = self.baselines,
            options = dOptions,
            params = dParams,
            configs = dConfigs,
            **kwargs
            )

    def add_observer(self, observerClass = None, observerInputs = None):
        if observerClass is None:
            observerClass, observerInputs = self.defaultObserver
        self.observer = observerClass(self, **observerInputs)
        try: self.show = self.observer.show
        except NameError: pass
        try: self.report = self.observer.report
        except NameError: pass

    def _initialise(self):
        for key, IC in sorted(self.configs.items()):
            if not IC is None:
                IC.apply(self.locals[key])
        self.chron.value = 0.
        self._update()

    def _iterate(self):
        dt = self._integrate(_skipClips = True)
        self._update()
        self.clipVals()
        self.setBounds()
        self.chron += dt

    def _integrate(self, _skipClips = False):
        dt = self.locals.integrate()
        if not _skipClips:
            self.clipVals()
            self.setBounds()
        return dt

    def _update(self):
        if self.has_changed():
            self.locals.update()

    def has_changed(self, reset = True):
        if not hasattr(self, '_currenthash'):
            self._currenthash = 0
        latesthash = hash(tuple([
            hash_var(var) \
                for key, var in sorted(self.varsOfState.items())
            ]))
        changed = latesthash != self._currenthash
        if reset:
            self._currenthash = latesthash
        return changed

    def clipVals(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_var(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

    def _out(self):
        yield np.array(self.chron())
        for varName, var in sorted(self.varsOfState.items()):
            yield fieldops.get_global_var_data(var)

    def _load(self, loadDict):
        for key, loadData in sorted(loadDict.items()):
            if key == 'chron':
                self.chron.value = loadData
            else:
                var = self.locals[key]
                assert hasattr(var, 'mesh'), \
                    'Only meshVar supported at present.'
                nodes = var.mesh.data_nodegId
                for index, gId in enumerate(nodes):
                    var.data[index] = loadData[gId]

    def __getitem__(self, indexer):
        from ..traverse import Traverse
        if type(indexer) is slice:
            return Traverse(
                system = self,
                initState = indexer.start,
                endState = indexer.stop,
                freq = indexer.step,
                observerClasses = []
                )
        elif type(indexer) is tuple:
            raise TypeError
        else:
            try: self.load(indexer)
            except LoadFail: self[:indexer]()
            return self.out()

# class Case(Built):
#
#     _swapscript = '''from planetengine.systems import Case as CLASS'''
#
#     @staticmethod
#     def _process_inputs(inputs):
#
#
#     def __init__(self,
#             schema = None,
#             **inps
#             ):
#
#         super().__init__(**kwargs)

# Aliases
from functools import partial
from .viscoplastic import Viscoplastic
from .arrhenius import Arrhenius
from .isovisc import Isovisc
