# from ..utilities import check_reqs
import everest

from . import _built
from . import fieldops

from .visualisation import QuickFig

INITIAL_FLAG = '_initial_'

def load(name, path):
    return _built.load_built(name, path)

class System(everest.built.Built):

    name = 'system'

    def __init__(
            self,
            inputs,
            script,
            varsOfState,
            update,
            integrate
            ):

        self.varsOfState = varsOfState
        self.modeltime = everest.value.Value(0.)

        self._update = update
        self._integrate = integrate

        self.initials = {
            key[len(INITIAL_FLAG):]: val \
                for key, val in inputs.items() \
                    if key[:len(INITIAL_FLAG)] == INITIAL_FLAG
            }

        # ATTRIBUTES EXPECTED BY BUILT CLASS

        self.outkeys = [
            'modeltime',
            *sorted(self.varsOfState.keys())
            ]

        super().__init__(
            inputs,
            script
            )

    # METHODS EXPECTED BY BUILT CLASS:

    def initialise(self):
        for varName in sorted(self.initials):
            self.initials[varName].apply(
                self.varsOfState[varName]
                )
        self.modeltime.value = 0.
        self.update()

    def iterate(self):
        dt = self._iterate()
        self.clipVals()
        self.setBounds()
        self.modeltime.value += dt

    def load(self, loadDict):
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

    def out(self):
        outs = []
        for key in self.outkeys:
            if key == 'modeltime':
                outs.append([self.modeltime()])
            else:
                var = self.varsOfState[key]
                data = fieldops.get_global_sorted_array(var)
                outs.append(data)
        return outs

    # OTHER METHODS

    def clipVals(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_array(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(self.varsOfState.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

    def set_initials(self, ICdict):
        if ICdict.keys() == self.varsOfState.keys():
            self.initials = ICdict
        else:
            raise Exception(
                "Must provide an initial condition for every variable of state."
                )

    def update(self):
        self._update()

    def integrate(self, _skipClips = False):
        dt = self._integrate()
        if not _skipClips:
            self.clipVals()
            self.setBounds()
        return dt

    def _iterate(self):
        dt = self.integrate(_skipClips = True)
        self.update()
        return dt

    def go(self, steps):
        for step in range(steps):
            self.iterate()

    def makefig(self):
        self.fig = QuickFig(self.varsOfState)

    def show(self):
        if not hasattr(self, 'fig'):
            self.makefig()
        else:
            self.fig.update()
        self.fig.show()
