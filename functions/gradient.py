class Gradient(Function):

    opTag = 'Gradient'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)
        inVar = inVar.meshVar()
        # DEBUGGING
        assert not inVar is None

        var = inVar.var.fn_gradient

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        self.scales = [['.', '.']] * inVar.mesh.dim ** 2
        self.bounds = [['.'] * inVar.mesh.dim ** 2] * inVar.varDim

        super().__init__(**kwargs)

    @staticmethod
    def mag(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'mag', **kwargs)

    @staticmethod
    def rad(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'rad', **kwargs)

    @staticmethod
    def ang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'ang', **kwargs)

    @staticmethod
    def coang(*args, **kwargs):
        gradVar = Gradient(*args, **kwargs)
        return Component(gradVar, component = 'coang', **kwargs)
