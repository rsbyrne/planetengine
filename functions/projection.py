class Projection(Function):

    opTag = 'Projection'

    def __init__(self, inVar, *args, **kwargs):

        inVar = convert(inVar)

        var = uw.mesh.MeshVariable(
            inVar.mesh,
            inVar.varDim,
            )
        self._projector = uw.utils.MeshVariable_Projection(
            var,
            inVar,
            )

        self.stringVariants = {}
        self.inVars = [inVar]
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _partial_update(self):
        self._projector.solve()
        allwalls = self.meshUtils.surfaces['all']
        self.var.data[allwalls.data] = \
            self.inVar.evaluate(allwalls)
        if self.inVar.dType in ('int', 'boolean'):
            rounding = 1
        else:
            rounding = 6
        self.var.data[:] = np.round(
            self.var.data,
            rounding
            )
