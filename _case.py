from everest.builts._sliceable import Sliceable
from . import real
from . import traverse
from . import configs
from .utilities import Grouper

class Case(Sliceable):
    from .case import __file__ as _file_
    def __init__(
            self,
            system = None,
            params = None,
            **kwargs
            ):
        localsDict = system.parameterise(**params.inputs)
        self.system = system
        self.params = params
        self.locals = Grouper(localsDict)
        self.varsOfState = self.locals.varsOfState
        super().__init__(**kwargs)
        def sliceFn(arg):
            if isinstance(arg, real.CLASS):
                config = arg.configuration()
            elif isinstance(arg, traverse.CLASS):
                arg()
                config = arg.arg.configuration()
            elif isinstance(arg, configs.CLASS):
                config = arg
            else:
                raise TypeError
            return real.build(case = self, configs = config)
        self._slice_fns.append(sliceFn)
