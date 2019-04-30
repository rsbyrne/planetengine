import planetengine
import modelscripts
from planetengine import utilities
from planetengine import mapping
from planetengine.utilities import mesh_utils

import underworld as uw
from underworld import function as fn

# import numpy as np
# from planetengine.utilities import Grouper
# from planetengine.observer import ObsVar

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

from newstats import ScalarIntegral

class UtilVar:

    def __init__(
            self,
            var,
            varName = 'noname',
            recursions = 2,
            inheritedUpdate = None,
            attach = True
            ):

        '''
        Takes either a var or a tuple of a varName and a var, \
        which can be either a mesh variable, \
        a swarm variable, or a tuple of the form: \
        (Underworld function, substrate), \
        where 'substrate' is either a mesh, if the function \
        is dependent solely on mesh variables; a swarm, \
        if the function is partly or wholely dependent \
        on a swarm variable; or None, if there is no substrate \
        (e.g. an 'fn.misc.constant' -type object). \
        '''

        if rank == 0:
            print("Initialising UtilVar...")

        self.recursions = recursions
        if not inheritedUpdate is None:
            self.inheritedUpdate = inheritedUpdate

        if type(var) == tuple:
            self.var, self.substrate = var
        else:
            self.var = var
        self.varName = varName

        self._unpack_var()

        if not self.varType == 'special':

            mesh_utils(self.mesh)

            if self.varType == 'meshVar':
                self.meshVar = lambda: self.var
                self.gradient = lambda: self.var.fn_gradient
            else:
                self._make_projector()
                def meshVar():
                    self.update()
                    return self.projection
                self.meshVar = meshVar
                # FIX THIS SO GRADIENT CAN BE 'EVALUATED' (Underworld-style)
                self.gradient = lambda: self.meshVar().fn_gradient

            self._add_stats()

            if self.recursions > 0:
                self._recursion()

        if attach:
            if rank == 0:
                print("Attaching...")
            self.var.__dict__.update({'pe': self})
            if rank == 0:
                print("Done!")

    def _unpack_var(self):

        if rank == 0:
            print("Unpacking var...")

        isMeshVar = (
            type(self.var) == uw.mesh._meshvariable.MeshVariable
            )
        isSwarmVar = (
            type(self.var) == uw.swarm._swarmvariable.SwarmVariable
            )
        isFunction = issubclass(
            type(self.var),
            fn.Function
            )
        print(type(self.var))
        print(self.var)
        assert any([isMeshVar, isSwarmVar, isFunction]), \
            "Only mesh variables, swarm variables, and tuples \
            of the appropriate form (see docstring) are permitted."

        if isMeshVar or isSwarmVar:

            dType = self.var.dataType
            data = self.var.data

            if isMeshVar:
                varType = 'meshVar'
                dim = self.var.nodeDofCount
                substrate = self.var.mesh
                swarm = None
                mesh = self.var.mesh

            else:
                varType = 'swarmVar'
                dim = self.var.count
                substrate = self.var.swarm
                swarm = self.var.swarm
                mesh = self.var.swarm.mesh

        else:

            substrate = self.substrate
            data = self.var.evaluate(substrate)

            np_dType = str(data.dtype)
            if np_dType == 'int32':
                dType = 'int'
            elif np_dType == 'float64':
                dType = 'double'
            elif np_dType == 'bool':
                dType = 'boolean'
            else:
                raise Exception(
                    "Input data type not acceptable."
                    )
            dType = dType

            dim = data.shape[1]

            if substrate is None:
                varType = 'special'
                mesh = None
                swarm = None
            else:
                try:
                    varType = 'swarmFn'
                    mesh = substrate.mesh
                    swarm = substrate
                except:
                    varType = 'meshFn'
                    mesh = substrate
                    swarm = None

        outDict = {
            'varType': varType,
            'dType': dType,
            'dim': dim,
            'data': data,
            'substrate': substrate,
            'swarm': swarm,
            'mesh': mesh,
            }

        self.__dict__.update(outDict)

    def _make_projector(self):

        if rank == 0:
            print("Making projector...")

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

    def _add_stats(self):

        if rank == 0:
            print("Adding stats...")

        self.statsDict = {}

        if self.dType == 'double':
            scalarIntegralSuite = {}

            if self.dim == 1:
                scalarIntegralSuite['surface'] = \
                    ['volume', 'inner', 'outer']
                if self.recursions == 0:
                    scalarIntegralSuite['gradient'] = \
                        [None, 'mag']
                    scalarIntegralSuite['gradient'] += \
                        self.mesh.pe.comps.keys()
            elif self.dim == self.mesh.dim:
                if self.recursions == 0:
                    scalarIntegralSuite['surface'] = \
                        ['volume', 'inner', 'outer']
                    scalarIntegralSuite['comp'] = \
                        ['mag']
                    scalarIntegralSuite['comp'] += \
                        self.mesh.pe.comps.keys()

            for inputDict in utilities.suite_list(scalarIntegralSuite):
                anVar = ScalarIntegral(
                    self.meshVar(),
                    self.mesh,
                    inheritedUpdate = self.update,
                    **inputDict
                    )
                self.statsDict[anVar.opTag] = anVar

            else:
                pass

        else:
            pass

        self.__dict__.update(self.statsDict)

    def _recursion(self):

        if rank == 0:
            print("Adding recursions...")

        new_recursions = self.recursions - 1

        # Define all the recursion functions:

        recursionFuncs = {}

        if self.dim == 1:
            recursionFuncs['radGrad'] = fn.math.dot(
                self.mesh.pe.rad,
                self.gradient()
                )
            recursionFuncs['magGrad'] = fn.math.sqrt(
                fn.math.dot(
                    self.gradient(),
                    self.gradient()
                    )
                )
            if self.mesh.dim == 2:
                recursionFuncs['angGrad'] = fn.math.dot(
                    self.mesh.pe.ang,
                    self.gradient()
                    )
            elif self.mesh.dim == 3:
                recursionFuncs['angGrad1'] = fn.math.dot(
                    self.mesh.pe.ang1,
                    self.gradient()
                    )
                recursionFuncs['angGrad2'] = fn.math.dot(
                    self.mesh.pe.ang1,
                    self.gradient()
                    )
            else:
                raise Exception(
                    "Spatial dimensions higher than three \
                    are (unsurprisingly) not supported."
                    )

        else:
            assert self.dim == self.mesh.dim, \
                'Only scalars or vectors with \
                spatially referenced components \
                are currently supported.'

            recursionFuncs['mag'] = fn.math.sqrt(
                fn.math.dot(
                    self.var,
                    self.var
                    )
                )
            recursionFuncs['radComp'] = fn.math.dot(
                self.mesh.pe.rad,
                self.meshVar()
                )

            if self.dim == 2:

                recursionFuncs['angComp'] = fn.math.dot(
                    self.mesh.pe.ang,
                    self.meshVar()
                    )

            elif self.dim == 3:

                recursionFuncs['angComp1'] = fn.math.dot(
                    self.mesh.pe.ang1,
                    self.meshVar()
                    )
                recursionFuncs['angComp2'] = fn.math.dot(
                    self.mesh.pe.ang2,
                    self.meshVar()
                    )

            else:
                raise Exception(
                    "Dimensions greater than three not yet supported."
                    )

        # Now use the recursion funcs to build UtilVars
        # and make them attributes of the parent UtilVar:

        for varName, var in sorted(recursionFuncs.items()):

            newVar = UtilVar(
                (var, self.mesh),
                varName = varName,
                recursions = new_recursions,
                inheritedUpdate = self.update
                )

            setattr(self, varName, newVar)

        # Done!

        if rank == 0:
            print("Added recursions.")

    def update(self, initialising = False):

        if rank == 0:
            print("Updating...")

        if hasattr(self, 'inheritedUpdate'):
            self.inheritedUpdate()

        if not self.varType == 'meshVar' or self.varType == 'swarmVar':
            self.project()

        # if not self.varType == 'meshVar' or self.varType == 'swarmVar':
        #     self.data = self.var.evaluate(self.substrate)
        # newDataHash = hash(str(self.data))
        # if not newDataHash == self.dataHash:
        #     self.dataHash = newDataHash
        #     if not self.varType == 'meshVar':
        #         self.project()

    def evaluate(self, inputs):

        return self.meshVar().evaluate(inputs)

    def __call__(self):
        return self.meshVar()
