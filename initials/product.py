from planetengine.IC import IC

def build(*args, **kwargs):
    built = Product(*args, **kwargs)
    return built

class Product(IC):

    varDim = 1
    meshDim = 2

    def __init__(
            self,
            *args,
            ):

        raise Exception("Not supported yet!")

        pass
        # self.inputs =
        def evaluate(coordArray):
            return coordArray

        super().__init__()
