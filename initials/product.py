from planetengine.initials import IC

class Product(IC):

    species = 'product'

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

### IMPORTANT ###
from everest.builts import make_buildFn
CLASS = Product
build = make_buildFn(CLASS)
