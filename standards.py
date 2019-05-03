import underworld as uw
from underworld import function as fn
import planetengine

def standardise(
        inVar,
        attach = True,
        heavy = False,
        inheritedUpdate = None
        ):

    if type(inVar) == StandardInput:
        stInp = inVar
    elif hasattr(inVar, 'pe_stInp'):
        stInp = inVar.pe_stInp
    else:
        stInp = StandardInput(
            inVar,
            heavy = heavy,
            inheritedUpdate = inheritedUpdate
            )
    if attach:
        if not hasattr(stInp.var, 'pe_stInp'):
            stInp.var.__dict__.update({'pe_stInp': stInp})
    stInp.update()
    return stInp

class StandardInput:

    def __init__(
            self,
            var,
            inheritedUpdate = None,
            heavy = False,
            ):

        self.heavy = heavy
        self.inheritedUpdate = inheritedUpdate
        self.var = var
        self.substrate = None
        self.varName = 'noname'
        if type(self.var) == tuple:
            if len(self.var) == 2:
                if type(self.var[0]) == str:
                    self.varName, self.var = self.var
                else:
                    self.var, self.substrate = self.var
            elif len(self.var) == 3:
                self.varName, self.var, self.substrate = self.var
        if hasattr(self.var, 'subMesh'):
            self.substrateName = 'mesh'
            self.dim = self.var.dim
            self.substrate = self.var
            self.swarm = None
            self.mesh = self.var
            self.varType = 'mesh'
            self.data = self.var.data
        elif hasattr(self.var, 'particleCoordinates'):
            self.substrateName = 'swarm'
            self.dim = self.var.mesh.dim
            self.substrate = self.var
            self.swarm = self.var
            self.mesh = self.var.mesh
            self.varType = 'swarm'
            self.data = self.var.particleCoordinates.data
        elif not self.substrate is None: # hence var is a function:
            self.data = self.var.evaluate(self.substrate)
            self.dim = self.data.shape[1]
            try:
                self.substrateName = 'swarm'
                self.swarm = self.substrate
                self.mesh = self.swarm.mesh
                self.varType = 'swarmFn'
            except:
                self.substrateName = 'mesh'
                self.swarm = None
                self.mesh = self.substrate
                self.varType = 'meshFn'
        elif type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self.substrateName = 'mesh'
            self.dim = self.var.nodeDofCount
            self.substrate = self.var.mesh
            self.swarm = None
            self.mesh = self.var.mesh
            self.varType = 'meshVar'
            self.data = self.var.data
        elif type(self.var) == uw.swarm._swarmvariable.SwarmVariable:
            self.substrateName = 'swarm'
            self.dim = self.var.count
            self.substrate = self.var.swarm
            self.swarm = self.substrate
            self.mesh = self.swarm.mesh
            self.varType = 'swarmVar'
            self.data = self.var.data
        else:
            self.substrateName = 'None'
            self.varType = 'special'
            self.mesh = None
            self.swarm = None
            self.data = var.evaluate()

        if str(self.data.dtype) == 'int32':
            self.dType = 'int'
        elif str(self.data.dtype) == 'float64':
            self.dType = 'double'
        elif str(self.data.dtype) == 'bool':
            self.dType = 'boolean'
        else:
            raise Exception(
                "Input data type not acceptable."
                )

        if not self.varType == 'special':

            if not hasattr(self.mesh, 'pe_meshUtils'):
                planetengine.meshutils.MeshUtils(self.mesh)
            self.meshUtils = self.mesh.pe_meshUtils

            if not self.varType in {'mesh', 'swarm'}:

                if self.varType == 'meshVar':
                    self.meshVar = self.var
                else:
                    if not self.heavy:
                        self.meshVar = self.meshUtils.meshify(self.var)
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
        def project():
            self.projector.solve()
            if self.dType == 'int':
                self.projection.data[:] = np.round(
                    self.projection.data
                    )
        self.project = project
        self.project()

    def update(self):
        if not self.inheritedUpdate is None:
            self.inheritedUpdate()
        if hasattr(self, 'meshVar') and not self.varType == 'meshVar':
            if not self.heavy:
                self.meshVar = self.meshUtils.meshify(self.var)
            else:
                self.project()
        if self.varType in {'meshFn', 'swarmFn', 'special'}:
            self.data = self.var.evaluate(self.substrate)