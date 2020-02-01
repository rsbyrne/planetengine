import numpy as np

from everest.builts._iterator import Iterator

from everest.value import Value
from planetengine import fieldops
from planetengine import utilities

class Real(Iterator):

    def __init__(
            self,
            case,
            configs
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
            initialise,
            iterate,
            out,
            outkeys,
            load
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

CLASS = Real
build, get = CLASS.build, CLASS.get
