from everest.builts._inquirer import Inquirer
from ..real import Real

class State(Inquirer):
    def __init__(
            self,
            evaluateFn,
            **kwargs
            ):
        super().__init__(
            _inquirer_meta_fn = all,
            _inquirer_arg_typeCheck = lambda arg: isinstance(arg, Real),
            **kwargs
            )
        self._inquirer_fns.append(evaluateFn)
