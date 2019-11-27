import everest
wordhashstamp = everest.utilities.wordhashstamp
from . import fieldops
from .visualisation import QuickFig

INITIAL_FLAG = '_initial_'

class System(everest.built.Built):

    name = 'system'

    def __init__(
            self,
            inputs,
            script,
            varsOfState,
            obsVars,
            update,
            integrate
            ):

        self.varsOfState = varsOfState
        self.obsVars = obsVars
        self.modeltime = everest.value.Value(0.)

        self._update = update
        self._integrate = integrate

        self.configs = {
            key[len(INITIAL_FLAG):]: val \
                for key, val in inputs.items() \
                    if key[:len(INITIAL_FLAG)] == INITIAL_FLAG
            }
        self.params = {
            key: val \
                for key, val in inputs.items() \
                    if not key[:len(INITIAL_FLAG)] == INITIAL_FLAG
            }

        self.observers = []

        # ATTRIBUTES EXPECTED BY BUILT CLASS

        self.outkeys = [
            'modeltime',
            *sorted(self.varsOfState.keys())
            ]

        meta = {
            # 'params': wordhashstamp(self.params)
            # 'configs': wordhashstamp(self.configs)
            }

        super().__init__(
            inputs,
            script
            )

    # METHODS EXPECTED BY BUILT CLASS:

    def initialise(self):
        for varName in sorted(self.configs):
            self.configs[varName].apply(
                self.varsOfState[varName]
                )
        self.modeltime.value = 0.
        self.update()

    def iterate(self):
        dt = self._iterate()
        self.clipVals()
        self.setBounds()
        self.modeltime.value += dt
        # for observer in self.observers:
        #     observer.prompt()

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
                outs.append(self.modeltime())
            else:
                var = self.varsOfState[key]
                data = get_global_var_data(var)
                outs.append(data)
        return outs

    # OTHER METHODS

    # def add_observer(self, observer):
    #     self.observers.append(observer)
    #     if self.anchored:
    #         observer.anchor(self.frameID, self.path)

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
            self.configs = ICdict
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
