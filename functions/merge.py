class Merge(Function):

    opTag = 'Merge'

    def __init__(self, *args, **kwargs):

        inVars = convert(args)

        for inVar in inVars:
            if not inVar.varDim == 1:
                raise Exception

        dTypes = set([inVar.dType for inVar in inVars])
        if not len(dTypes) == 1:
            raise Exception
        dType = list(dTypes)[0]

        substrates = set([inVar.substrate for inVar in inVars])
        if not len(substrates) == 1:
            raise Exception

        substrate = list(substrates)[0]
        if substrate is None:
            raise Exception

        meshbased = all(
            [inVar.meshbased for inVar in inVars]
            )
        dimension = len(inVars)
        if meshbased:
            var = substrate.add_variable(dimension, dType)
        else:
            var = substrate.add_variable(dType, dimension)

        self.stringVariants = {}
        self.inVars = list(inVars)
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        for index, inVar in enumerate(self.inVars):
            self.var.data[:, index] = \
                inVar.evaluate()[:, 0]

    @staticmethod
    def annulise(inVar):
        inVar = convert(inVar)
        comps = []
        comps.append(Component(inVar, component = 'ang'))
        comps.append(Component(inVar, component = 'rad'))
        if inVar.mesh.dim == 3:
            comps.append(Component(inVar, component = 'coang'))
        var = Merge(*comps)
        return var

    @staticmethod
    def cartesianise(inVar):
        inVar = convert(inVar)
        comps = []
        comps.append(Component(inVar, component = 'x'))
        comps.append(Component(inVar, component = 'y'))
        if inVar.mesh.dim == 3:
            comps.append(Component(inVar, component = 'z'))
        var = Merge(*comps)
        return var
