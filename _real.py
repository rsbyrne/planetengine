import numpy as np

from everest.builts._iterator import Iterator
from everest.builts._sliceable import Sliceable
from everest.value import Value

from . import fieldops
from . import utilities
from . import traverse as traverseModule
from . import configs

class Real(Iterator, Sliceable):

    from .real import __file__ as _file_

    @staticmethod
    def _process_inputs(inputs):
        inConf = inputs['configs']
        if isinstance(inConf, configs.CLASS):
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

        modeltime = Value(0.)
        varsOfState = case.varsOfState

        def update():
            case.locals.update()

        def integrate(_skipClips = False):
            dt = case.locals.integrate()
            if not _skipClips:
                self.clipVals()
                self.setBounds()
            return dt

        def _iterate():
            dt = integrate(_skipClips = True)
            update()
            return dt

        def iterate():
            dt = _iterate()
            self.clipVals()
            self.setBounds()
            modeltime.value += dt

        def initialise():
            configs(case)
            modeltime.value = 0.
            update()

        def load(loadDict):
            for key, loadData in sorted(loadDict.items()):
                if key == 'modeltime':
                    modeltime.value = loadData
                else:
                    var = varsOfState[key]
                    assert hasattr(var, 'mesh'), \
                        'Only meshVar supported at present.'
                    nodes = var.mesh.data_nodegId
                    for index, gId in enumerate(nodes):
                        var.data[index] = loadData[gId]

        def out():
            yield np.array(modeltime())
            for varName, var in sorted(varsOfState.items()):
                yield fieldops.get_global_var_data(var)

        outkeys = ['modeltime', *sorted(varsOfState.keys())]

        self.system = case.system
        self.params = case.params
        self.locals = case.locals
        self.case = case
        self.configs = configs
        self.varsOfState = varsOfState
        self.modeltime = modeltime

        super().__init__(
            initialiseFn = initialise,
            iterateFn = iterate,
            outFn = out,
            outkeys = outkeys,
            loadFn = load,
            **kwargs
            )

        def sliceFn(state):
            return traverseModule.build(arg = self, state = state)
        self._slice_fns.append(sliceFn)

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
        from .initials import state as ICstate
        from . import configs
        from .states import threshold
        ICdict = {}
        for key in sorted(self.varsOfState):
            if key in altKeys:
                ICkey = altKeys[key]
            else:
                ICkey = key
            state = threshold.build(val = self.count())
            ICdict[ICkey] = ICstate.build(
                real = self,
                state = state,
                varName = key
                )
        return configs.build(**ICdict)

    def traverse(self, state):
        return self[state]
