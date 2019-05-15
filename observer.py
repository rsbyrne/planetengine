import underworld as uw
from underworld import function as fn
import numpy as np

class ObsVar:

    '''
    Defines a class that wraps around typical
    Underworld model objects and provides
    many useful aliases and operations
    for data analysis.
    '''

    def __init__(self, varName, var):

        '''
        Takes a varName and a 'var'
        which can be either a mesh variable,
        a swarm variable, or a tuple of the form:
        (Underworld function, substrate),
        where 'substrate' is either a mesh, if the function
        is dependent solely on mesh variables; a swarm,
        if the function is partly or wholely dependent
        on a swarm variable; or None, if there is no substrate
        (e.g. an 'fn.misc.constant' -type object).
        '''

        isMeshVar = type(var) == uw.mesh._meshvariable.MeshVariable
        isSwarmVar = type(var) == uw.swarm._swarmvariable.SwarmVariable
        isTuple = type(var) == tuple

        if isMeshVar or isSwarmVar:

            self.var = var
            self.dType = self.var.dataType
            self.data = self.var.data

            if isMeshVar:
                self.varType = 'meshVar'
                self.dim = self.var.nodeDofCount
                self.substrate = self.var.mesh
                self.mesh = self.var.mesh

            else:
                self.varType = 'swarmVar'
                self.dim = self.var.count
                self.substrate = self.var.swarm
                self.swarm = self.var.swarm
                self.mesh = self.var.swarm.mesh

        elif isTuple:

            self.var, self.substrate = var

            assert issubclass(type(var[0]), uw.function.Function), \
                "First arg of tuple must be an Underworld function."

            self.data = self.var.evaluate(self.substrate)

            np_dType = str(self.data.dtype)
            if np_dType == 'int32':
                dType = 'int'
            elif np_dType == 'float64':
                dType = 'double'
            elif np_dType == 'bool':
                dType = 'boolean'
            else:
                raise Exception("Input data type not acceptable.")
            self.dType = dType

            self.dim = self.data.shape[1]

            if self.substrate is None:
                self.varType = 'special'
            else:
                try:
                    self.varType = 'swarmFn'
                    self.mesh = self.substrate.mesh
                    self.swarm = self.substrate
                except:
                    self.varType = 'meshFn'
                    self.mesh = self.substrate

        else:

            raise Exception(
                "Only mesh variables, swarm variables, and tuples \
                of the appropriate form (see docstring) are permitted."
                )

        self.dataHash = hash(str(self.data))

        if not self.varType == 'special':

            if self.varType == 'meshVar':
                self.meshVar = self.var

            else:

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
                        self.projection.data[:] = np.round(self.projection.data)
                self.project = project
                self.project()

                self.meshVar = self.projection 

    def update(self):
        if not self.varType == 'meshVar' or self.varType == 'swarmVar':
            self.data = self.var.evaluate(self.substrate)
        newDataHash = hash(str(self.data))
        if not newDataHash == self.dataHash:
            self.dataHash = newDataHash
            if not self.varType == 'meshVar':
                self.project()

    def __call__(self):
        self.update()
        return self.meshVar