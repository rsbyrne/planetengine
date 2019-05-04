import underworld as uw
from underworld import function as fn
import planetengine
import numpy as np

def standardise(
        *args,
        attach = True,
        heavy = True,
        inheritedUpdate = None
        ):

    stInp = None

    if len(args) == 1 and type(args[0]) == tuple:
        args = args[0]
    inputTypes = {type(arg): arg for arg in args}
    if StandardInput in inputTypes:
        stInp = inputTypes[StandardInput]
    else:
        for arg in args:
            if hasattr(arg, 'pe_stInp'):
                stInp = arg.pe_stInp
    if stInp == None:
        varName = 'noname'
        substrate = None
        if len(args) == 1:
            var = args[0]
        elif len(args) == 2:
            if type(args[0]) == str:
                varName, var = args
            else:
                var, substrate = args
        elif len(args) == 3:
            varName, var, substrate = args
        else:
            raise Exception("Input not understood.")
        stInp = StandardInput(
            var,
            varName,
            substrate,
            heavy = heavy,
            inheritedUpdate = inheritedUpdate
            )
    if attach:
        if not hasattr(stInp.var, 'pe_stInp'):
            stInp.var.__dict__.update({'pe_stInp': stInp})
    return stInp

class StandardInput:

    def __init__(
            self,
            var,
            varName,
            substrate,
            inheritedUpdate = None,
            heavy = True,
            ):

        self.heavy = heavy
        self.inheritedUpdate = inheritedUpdate
        self.var = var
        self.substrate = substrate
        self.varName = varName
        if not self.substrate is None: # hence var is a function:
            self.data = self.var.evaluate(self.substrate)
            self.dim = self.data.shape[1]
            try:
                self.substrateName = 'swarm'
                self.swarm = self.substrate
                self.mesh = self.swarm.mesh
                self.varType = 'swarmFn'
                self.types = {'swarm', 'function'}
            except:
                self.substrateName = 'mesh'
                self.swarm = None
                self.mesh = self.substrate
                self.varType = 'meshFn'
                self.types = {'mesh', 'function'}
        elif type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self.substrateName = 'mesh'
            self.dim = self.var.nodeDofCount
            self.substrate = self.var.mesh
            self.swarm = None
            self.mesh = self.var.mesh
            self.varType = 'meshVar'
            self.types = {'mesh', 'variable'}
            self.data = self.var.data
        elif type(self.var) == uw.swarm._swarmvariable.SwarmVariable:
            self.substrateName = 'swarm'
            self.dim = self.var.count
            self.substrate = self.var.swarm
            self.swarm = self.substrate
            self.mesh = self.swarm.mesh
            self.varType = 'swarmVar'
            self.types = {'swarm', 'variable'}
            self.data = self.var.data
        else:
            raise Exception("Input not recognised.")
        if str(self.data.dtype) == 'int32':
            self.dType = 'int'
            self.types.add('discrete')
            if 0 in self.data:
                self.types.add('binary')
        elif str(self.data.dtype) == 'float64':
            self.dType = 'double'
            self.types.add('continuous')
        elif str(self.data.dtype) == 'bool':
            self.dType = 'boolean'
            self.types.add('discrete')
            self.types.add('binary')
        else:
            raise Exception(
                "Input data type not acceptable."
                )
        if self.dim == 1:
            self.types.add('scalar')
        elif self.dim == self.mesh.dim:
            self.types.add('vector')
        else:
            raise Exception(
                "Only scalars and spatially-referenced vectors accepted."
                )

        if not hasattr(self.mesh, 'pe_meshUtils'):
            planetengine.meshutils.MeshUtils(self.mesh)
        self.meshUtils = self.mesh.pe_meshUtils

        if not self.varType in {'mesh', 'swarm'}:

            if self.varType == 'meshVar':
                self.meshVar = self.var
            else:
                if not self.heavy:
                    self.meshVar, self.projector = self.meshUtils.meshify(self.var)
                else:
                    self._make_projector()
                    self.meshVar = self.projection
            self.gradient = self.meshVar.fn_gradient

    def _make_projector(self):
        self.projection = uw.mesh.MeshVariable(
            self.mesh,
            self.dim,
            )
        self.projector = uw.utils.MeshVariable_Projection(
            self.projection,
            self.var,
            )

    def project(self):
        self.projector.solve()
        if 'discrete' in self.types:
            self.meshVar.data[:] = np.round(
                self.meshVar.data
                )

    def update(self):
        if not self.inheritedUpdate is None:
            self.inheritedUpdate()
        if not self.varType == 'meshVar':
            self.project()
        if self.varType in {'meshFn', 'swarmFn', 'special'}:
            self.data = self.var.evaluate(self.substrate)