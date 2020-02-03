from planetengine.states import State

class Threshold(State):
    def __init__(
            self,
            prop : str = 'count',
            op : str = 'eq',
            val = None,
            **kwargs
            ):
        op = '__{a}__'.format(a = op)
        getProperty = lambda arg: getattr(arg, prop)
        getOpFn = lambda arg: getattr(getProperty(arg), op)
        boolFn = lambda arg: getOpFn(arg)(val)
        super().__init__(boolFn, **kwargs)

CLASS = Threshold
build, get = CLASS.build, CLASS.get
