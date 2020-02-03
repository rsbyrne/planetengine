from everest.builts._task import Task

class Traverse(Task):
    from .traverse import __file__ as _file_
    def __init__(
            self,
            arg = None,
            state = None,
            **kwargs
            ):
        self.arg = arg
        self.state = state
        super().__init__(**kwargs)
        if isinstance(arg, Task): arg = arg().arg
        self._task_cycler_fns.append(arg)
        self._task_stop_fns.append(lambda: state(arg))

    def configuration(self, altKeys = dict()):
        from .initials import state as ICstate
        from . import configs
        ICdict = {}
        for key in sorted(self.arg.varsOfState):
            if key in altKeys:
                ICkey = altKeys[key]
            else:
                ICkey = key
            ICdict[ICkey] = ICstate.build(
                real = self.arg,
                state = self.state,
                varName = key
                )
        return configs.build(**ICdict)
