from everest.builts.perambulator import Perambulator

class Traverse(Perambulator):

    def __init__(self,
            cosmos = None,
            vector = None,
            state = None,
            **kwargs
            ):

        system = cosmos.vectorise(vector)

        super().__init__(
            iterator = system,
            state = state,
            **kwargs
            )
