# from ..utilities import check_reqs
from ._built import Built
from . import fieldops
from . import value
from .visualisation import QuickFig

class System(Built):

    name = 'system'

    def __init__(
            self,
            varsOfState,
            obsVars,
            _update,
            _integrate,
            _locals,
            args,
            kwargs,
            inputs,
            script,
            _iterate = None
            ):

        self.varsOfState = varsOfState
        self.obsVars = obsVars
        self._update = _update
        self._integrate = _integrate
        if not _iterate is None:
            self._iterate = _iterate

        self.step = value.Value(0)
        self.modeltime = value.Value(0.)

        self.initials = None

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

        for key in _locals:
            if not hasattr(self, key):
                setattr(self, key, _locals[key])

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

    def initialise(self, ICdict = None):
        if ICdict is None:
            ICdict = self.initials
        else:
            self.set_initials(ICdict)
        for varName in sorted(ICdict):
            ICdict[varName].apply(self.varsOfState[varName])
        self.step.value = 0
        self.modeltime.value = 0.
        self.update()

    def reset(self):
        self.initialise()

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

    def iterate(self):
        dt = self._iterate()
        self.clipVals()
        self.setBounds()
        self.modeltime.value += dt
        self.step.value += 1

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
