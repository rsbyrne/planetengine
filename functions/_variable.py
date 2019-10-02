import weakref

import underworld as uw
fn = uw.function
UWFn = fn._function.Function

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

    def __init__(self, inVar, varName = None, *args, **kwargs):

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
            vanillaVar = vanilla.default(var)
            projVar = vanillaVar.meshVar()
            var = projVar.var
            self._projUpdate = projVar.update
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
            self._meshVar = lambda: self
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            self.substrate = var.swarm
            self.mesh = var.swarm.mesh
            self.meshbased = False
            self.varType = 'swarmVar'
        else:
            raise Exception

        self._hashVars = [var]

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = var

        if not varName == self.defaultName:
            var._planetVar = weakref.ref(self)
        # self._set_meshdata()

        sample_data = self.data[0:1]
        self.dType = _planetvar.get_dType(sample_data)
        self.varDim = self.data.shape[1]
        self.meshUtils = meshutils.get_meshUtils(self.mesh)

        if hasattr(var, 'scales'):
            self.scales = var.scales
        if hasattr(var, 'bounds'):
            self.bounds = var.bounds

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
        if hasattr(self, '_projUpdate'):
            self._projUpdate()
        if not type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self._set_meshdata()
