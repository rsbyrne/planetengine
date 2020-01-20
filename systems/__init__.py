import weakref

import everest
from .. import fieldops
from .. import utilities
from ..visualisation import QuickFig

INITIAL_FLAG = '_initial_'

class System(everest.built.Built):

    observers = []
    type = 'system'

    def __init__(
            self,
            inputs,
            script,
            varsOfState,
            obsVars,
            update,
            integrate,
            dither = None,
            localsDict = {}
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
        # self.params = {
        #     key: val \
        #         for key, val in inputs.items() \
        #             if not key[:len(INITIAL_FLAG)] == INITIAL_FLAG
        #     }

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

        self.locals = utilities.Grouper(localsDict)
        if not dither is None:
            self.dither = dither
            dither.attach(self)

        super().__init__(
            inputs,
            script
            )

        # self.params = {
        #     key: val \
        #         for key, val in self.inputs.items() \
        #             if not key[:len(INITIAL_FLAG)] == INITIAL_FLAG
        #     }

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
                data = fieldops.get_global_var_data(var)
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

    def update(self):
        if self.has_changed():
            if not hasattr(self, 'dither'):
                self._update()
            else:
                self.dither._system = self
                with self.dither:
                    self._update()
        self._prompt_observers()

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

    def _post_anchor_hook(self):
        for ref in self.observers:
            observer = ref()
            if not observer is None:
                observer.coanchor(self)
                # self._anchoring_observers_stuff(observer)

    # def _anchoring_observers_stuff(self, observer):
    #     pass
    #     # WILL OVERRIDE if names clash!
    #     for key in sorted(observer.outDict):
    #         linkDest = '/' + observer.hashID + '/outs/' + key
    #         groupnames = self._add_subgroup('observations')
    #         self._add_link(linkDest, key, groupnames)

    def _prompt_observers(self):
        for ref in self.observers:
            observer = ref()
            if not observer is None:
                observer.prompt()

    def attach_observer(self, observer):
        self.observers.append(weakref.ref(observer))
        if self.anchored:
            self._anchoring_observers_stuff(observer)

    #
    # def makefig(self):
    #     self.fig = QuickFig(self.varsOfState)
    #
    # def show(self):
    #     if not hasattr(self, 'fig'):
    #         self.makefig()
    #     else:
    #         self.fig.update()
    #     self.fig.show()

from . import isovisc
from . import arrhenius
from . import MS98
# from . import rayleightaylor
