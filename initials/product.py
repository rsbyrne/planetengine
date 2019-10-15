from planetengine._IC import IC

def build(*args, name = None, **kwargs):
    built = Product(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Product(IC):

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
