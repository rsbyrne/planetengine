from ._IC import _IC

def build(*args, **kwargs):
    return IC(*args, **kwargs)

class IC(_IC):

    varDim = 1
    meshDim = 2

    def __init__(
            self,
            *args,
            ):

        pass
        # self.inputs =

        super().__init__()

    def evaluate(self, coordArray):
        return coordArray
