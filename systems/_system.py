# from ..utilities import check_reqs
from ..builts import Built
from .. import fieldops
from planetengine.utilities import Grouper

class System(Built):

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
            scripts,
            ):

        self.varsOfState = varsOfState
        self.obsVars = obsVars
        self._update = _update
        self._integrate = _integrate
        self.locals = Grouper(_locals)

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            scripts = scripts
            )

    def clipVals(self):
        for varName, var in sorted(varsOfState.items()):
            if hasattr(var, 'scales'):
                fieldops.clip_array(var, var.scales)

    def setBounds(self):
        for varName, var in sorted(varsOfState.items()):
            if hasattr(var, 'bounds'):
                fieldops.set_boundaries(var, var.bounds)

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
        return dt
