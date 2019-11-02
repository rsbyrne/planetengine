import weakref

import underworld as uw
_fn = uw.function
UWFn = _fn._function.Function

from . import _planetvar
from . import _basetypes
from . import vanilla
from .. import utilities
hasher = utilities.hashToInt
from .. import meshutils

class Variable(_basetypes.BaseTypes):

    opTag = 'Variable'

    defaultName = 'anon'

    convertTypes = {
        uw.mesh._meshvariable.MeshVariable,
        uw.swarm._swarmvariable.SwarmVariable
        }

    def __init__(self, inVar, varName = None, vector = None, *args, **kwargs):

        var = UWFn.convert(inVar)

        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) == 0:
            raise Exception

        if varName is None:
            if hasattr(var, 'name'):
                varName = var.name
            else:
                varName = self.defaultName

        if not type(var) in self.convertTypes:
            from . import projection
            vanillaVar = vanilla.default(var)
            inVar = projection.default(vanillaVar)
            var = inVar.var
            if hasattr(vanillaVar, 'scales'):
                var.scales = vanillaVar.scales
            if hasattr(vanillaVar, 'bounds'):
                var.bounds = vanillaVar.bounds

        self.data = var.data

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            self.substrate = self.mesh = var.mesh
            self.meshdata = self.data
            self.meshbased = True
            self.varType = 'meshVar'
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            self.substrate = var.swarm
            self.mesh = var.swarm.mesh
            self.meshbased = False
            self.varType = 'swarmVar'
        else:
            raise Exception

        self._hashVars = [var]

        if not varName == self.defaultName:
            var._planetVar = weakref.ref(self)
        # self._set_meshdata()

        sample_data = self.data[0:1]
        self.dType = _planetvar.get_dType(sample_data)
        self.varDim = self.data.shape[1]

        if vector is None:
            if not self.mesh is None:
                vector = self.varDim == self.mesh.dim
            else:
                vector = False
        elif vector:
            if not self.varDim == self.mesh.dim:
                raise Exception
        self.vector = vector

        self.meshUtils = meshutils.get_meshUtils(self.mesh)

        if hasattr(var, 'scales'):
            self.scales = var.scales
        if hasattr(var, 'bounds'):
            self.bounds = var.bounds

        self.stringVariants = {'varName': varName, 'vector': vector}
        self.inVars = []
        self.parameters = []
        self.var = var

        super().__init__(**kwargs)

    def _check_hash(self, lazy = False):
        if lazy and hasattr(self, '_currenthash'):
            return self._currenthash
        else:
            currenthash = hasher(self.data)
            self._currenthash = currenthash
        return currenthash

    def _set_meshdata(self):
        self.meshdata = self.var.evaluate(self.mesh)

    def _partial_update(self):
        if hasattr(self.var, 'project'):
            self.var.project()
        if not type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self._set_meshdata()
