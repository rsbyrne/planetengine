import numpy as np

from everest.builts._iterator import Iterator
from everest.builts._sliceable import Sliceable
from everest.value import Value
from everest.builts.states import operator

from . import fieldops
from . import utilities
from . import traverse as traverseModule
from . import configs as configsMod
from .initials import state as ICstate

class Real(Iterator, Sliceable):

    from .real import __file__ as _file_

    @staticmethod
    def _process_inputs(inputs):
        inConf = inputs['configs']
        if isinstance(inConf, configsMod.CLASS):
            pass
        elif isinstance(inConf, Real) or isinstance(inConf, traverseModule.CLASS):
            inputs['configs'] = inConf.configuration()
        else:
            raise TypeError

    def __init__(
            self,
            case,
            configs,
            **kwargs
            ):

        localsDict = case.optionalisation.system.buildFn()
        localsObj = utilities.Grouper(localsDict)

        modeltime = Value(0.)
        varsOfState = {
            key: localsDict[key] \
                for key in case.optionalisation.system.varsOfStateKeys
            }

        outkeys = ['modeltime', *sorted(varsOfState.keys())]

        self.system = case.optionalisation.system
        self.optionalisation = case.optionalisation
        self.case = case
        self.options = case.optionalisation.options
        self.params = case.params
        self.configs = configs
        self.localsDict = localsDict
        self.locals = localsObj

        self.varsOfState = varsOfState
        self.modeltime = modeltime
        self._outkeys = outkeys

        super().__init__(**kwargs)

        self._slice_fns.append(self.traverse)

    def _update(self):
        self.locals.update()

    def _integrate(self, _skipClips = False):
        dt = self.locals.integrate()
        if not _skipClips:
            self.clipVals()
            self.setBounds()
        return dt

    def _iterate(self):
        dt = self._integrate(_skipClips = True)
        self._update()
        self.clipVals()
        self.setBounds()
        self.modeltime.value += dt

    def _initialise(self):
        initDict = {
            **self.case.optionalisation.system.defaultConfigs,
            **self.configs.inputs
            }
        for key, val in sorted(initDict.items()):
            val.apply(self.localsDict[key])
        self.modeltime.value = 0.
        self._update()

    def _load(self, loadDict):
        for key, loadData in sorted(self.loadDict.items()):
            if key == 'modeltime':
                self.modeltime.value = loadData
            else:
                var = self.localsDict[key]
                assert hasattr(var, 'mesh'), \
                    'Only meshVar supported at present.'
                nodes = var.mesh.data_nodegId
                for index, gId in enumerate(nodes):
                    var.data[index] = loadData[gId]

    def _out(self):
        yield np.array(self.modeltime())
        for varName, var in sorted(self.varsOfState.items()):
            yield fieldops.get_global_var_data(var)

    def clipVals(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_array(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

    def has_changed(self, reset = True):
        if not hasattr(self, '_currenthash'):
            self._currenthash = 0
        latesthash = hash(tuple([
            utilities.hash_var(var) \
                for key, var in sorted(self.varsOfState.items())
            ]))
        changed = latesthash != self._currenthash
        if reset:
            self._currenthash = latesthash
        return changed

    def configuration(self, altKeys = dict()):
        ICdict = {}
        for key in sorted(self.varsOfState):
            if key in altKeys:
                ICkey = altKeys[key]
            else:
                ICkey = key
            state = operator.build(val = self.count())
            ICdict[ICkey] = ICstate.build(
                real = self,
                state = state,
                varName = key
                )
        return configsMod.build(**ICdict)

    def traverse(self, state):
        return traverseModule.build(arg = self, state = state)
