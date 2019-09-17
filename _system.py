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
            ):

        self.varsOfState = varsOfState
        self.obsVars = obsVars
        self._update = _update
        self._integrate = _integrate

        self.step = value.Value(0)
        self.modeltime = value.Value(0.)

        self.initials = None
        self.fig = QuickFig(varsOfState, style = 'smallblack')

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
            raise Exception

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

    def integrate(self):
        dt = self._integrate()
        self.clipVals()
        self.setBounds()
        return dt

    def iterate(self):
        dt = self.integrate()
        self.update()
        self.modeltime.value += dt
        self.step.value += 1
        return dt

    def go(self, steps):
        for step in range(steps):
            self.iterate()

    def show(self):
        self.fig.show()
