from ._IC import _IC

def build(*args, name = None, **kwargs):
    built = IC(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

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
