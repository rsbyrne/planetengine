import numpy as np
from planetengine.initials import IC

class Constant(IC):

    species = 'constant'

    def __init__(
            self,
            value = 0.,
            **kwargs
            ):

        def evaluate(*args):
            return value

        super().__init__(evaluate, **kwargs)

CLASS = Constant
build, get = CLASS.build, CLASS.get
