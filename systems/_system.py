from ..utilities import check_reqs
from ..builts import Built
from .. import fieldops

class System(Built):

    _required_attributes = {
        'inputs',
        'scripts',
        'varsOfState',
        'obsVars',
        'inArgs',
        '_update',
        '_integrate',
        }

    _accepted_inputTypes = {
        type([]),
        type(0),
        type(0.),
        type('0')
        }

    def __init__(self):

        if 'self' in self.inputs:
            del self.inputs['self']
        if 'args' in self.inputs:
            del self.inputs['args']
        if '__class__' in self.inputs:
            del self.inputs['__class__']

        print(self.inputs)
        for key, val in self.inputs.items():
            if type(val) == tuple:
                self.inputs[key] = list(val)
            if not type(val) in self._accepted_inputTypes:
                raise Exception(
                    "Type " + str(type(val)) + " not accepted."
                    )

        check_reqs(self)

        super().__init__()

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
