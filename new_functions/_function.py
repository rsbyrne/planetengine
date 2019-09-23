from . import _planetvar
from .. import meshutils

class Function(_planetvar.PlanetVar):

    def __init__(self, *args, **kwargs):

        for inVar in self.inVars:
            if not isinstance(inVar, _planetvar.PlanetVar):
                raise Exception(
                    "Type " + str(type(inVar)) + " is not _planetvar.PlanetVar."
                    )

        self._detect_substrates()
        self._detect_attributes()
        if not self.varType == 'constFn':
            self._detect_scales_bounds()
        self._hashVars = self.inVars

        super().__init__(**kwargs)

    def _detect_substrates(self):
        meshes = set()
        substrates = set()
        for inVar in self.inVars:
            if hasattr(inVar, 'mesh'):
                if not inVar.mesh is None:
                    meshes.add(inVar.mesh)
            if hasattr(inVar, 'substrate'):
                if not inVar.substrate is None:
                    substrates.add(inVar.substrate)
        if len(meshes) == 1:
            self.mesh = list(meshes)[0]
            self.meshUtils = meshutils.get_meshUtils(self.mesh)
        elif len(meshes) == 0:
            self.mesh = None
        else:
            raise Exception
        if len(substrates) == 1:
            self.substrate = list(substrates)[0]
        elif len(substrates) == 0:
            self.substrate = None
        else:
            raise Exception

    def _detect_attributes(self):
        if not self.mesh is None and self.substrate is self.mesh:
            self.meshbased = True
            self.varType = 'meshFn'
            sample_data = self.var.evaluate(self.mesh.data[0:1])
        else:
            self.meshbased = False
            if self.substrate is None:
                self.varType = 'constFn'
                sample_data = self.var.evaluate()
            else:
                self.varType = 'swarmFn'
                sample_data = self.var.evaluate(self.substrate.data[0:1])
        self.dType = _planetvar.get_dType(sample_data)
        self.varDim = sample_data.shape[1]

    def _detect_scales_bounds(self):
        fields = []
        for inVar in self.inVars:
            if type(inVar) == _basetypes.Variable:
                fields.append(inVar)
            elif isinstance(inVar, Function):
                fields.append(inVar)
        inscales = []
        inbounds = []
        for inVar in fields:
            if hasattr(inVar, 'scales'):
                if inVar.varDim == self.varDim:
                    inscales.append(inVar.scales)
                else:
                    inscales.append(inVar.scales * self.varDim)
            else:
                inscales.append(
                    [['.', '.']] * self.varDim
                    ) # i.e. perfectly free
            if hasattr(inVar, 'bounds'):
                if inVar.varDim == self.varDim:
                    inbounds.append(inVar.bounds)
                else:
                    inbounds.append(inVar.bounds * self.varDim)
            else:
                inbounds.append(
                    [['.'] * self.mesh.dim ** 2] * self.varDim
                    ) # i.e. perfectly free
        scales = []
        for varDim in range(self.varDim):
            fixed = not any([
                inscale[varDim] == ['.', '.'] \
                    for inscale in inscales
                ])
            if fixed:
                scales.append('!')
            else:
                scales.append('.')
        bounds = []
        for varDim in range(self.varDim):
            dimBounds = []
            for index in range(self.mesh.dim ** 2):
                fixed = not any([
                    inbound[varDim][index] == '.' \
                        for inbound in inbounds
                    ])
                if fixed:
                    dimBounds.append('!')
                else:
                    dimBounds.append('.')
            bounds.append(dimBounds)
        if not hasattr(self, 'scales'):
            self.scales = scales
        if not hasattr(self, 'bounds'):
            self.bounds = bounds
