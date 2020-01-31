import numpy as np

from everest.builts._iterator import Iterator
from everest.value import Value
from .. import fieldops
from .. import utilities
from ..visualisation import QuickFig
from .. import initials

class System(Iterator):

    def __init__(
            self,
            varsOfState,
            obsVars,
            updateFn,
            integrateFn,
            localsDict = {}
            ):

        self.varsOfState = varsOfState
        self.obsVars = obsVars
        self.modeltime = Value(0.)

        self.params, self.configs = dict(), dict()
        for varName, var in self.inputs.items():
            if varName[:len('_initial_')] == '_initial_':
                if not isinstance(var, initials.IC):
                    raise TypeError(
                        varName, ' must be an instance of IC class.'
                        )
                self.configs[varName[len('_initial_'):]] = var
            else:
                self.params[varName] = var

        self.locals = utilities.Grouper(localsDict)

        def update():
            updateFn()

        def integrate(_skipClips = False):
            dt = integrateFn()
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
            self.modeltime.value += dt

        def initialise():
            for varName, initialCondition in sorted(self.configs.items()):
                initialCondition.apply(
                    self.varsOfState[varName]
                    )
            self.modeltime.value = 0.
            update()

        def load(loadDict):
            for key, loadData in sorted(loadDict.items()):
                if key == 'modeltime':
                    self.modeltime.value = loadData
                else:
                    var = self.varsOfState[key]
                    assert hasattr(var, 'mesh'), \
                        'Only meshVar supported at present.'
                    nodes = var.mesh.data_nodegId
                    for index, gId in enumerate(nodes):
                        var.data[index] = loadData[gId]

        def out():
            yield np.array(self.modeltime())
            for varName, var in sorted(self.varsOfState.items()):
                yield fieldops.get_global_var_data(var)

        outkeys = ['modeltime', *sorted(self.varsOfState.keys())]

        super().__init__(
            initialise,
            iterate,
            out,
            outkeys,
            load,
            params = self.params,
            configs = self.configs
            )

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
