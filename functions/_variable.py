import weakref

import underworld as uw
fn = uw.function
UWFn =fn._function.Function

from . import _planetvar
from . import _basetypes
from . import vanilla
from .. import utilities
from .. import meshutils
from .. import mpi

class Variable(_basetypes.BaseTypes):

    opTag = 'Variable'

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

        self.defaultName = var.__hash__()
        self.varName = varName

        if not type(var) in self.convertTypes:
            raise Exception

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

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = var

        self._update_hash()

        super().__init__(**kwargs)

    def _check_hash(self, lazy = False):
        if not lazy:
            self._update_hash()
        return self._currenthash

    def _update_hash(self):
        self._currenthash = utilities.hash_var(self.var)

    def _set_meshdata(self):
        self.meshdata = self.var.evaluate(self.mesh)

    def _partial_update(self):
        if hasattr(self.var, 'project'):
            self.var.project()
        if not type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self._set_meshdata()
