import planetengine
import modelscripts
from planetengine import utilities
from planetengine import mapping
from planetengine import meshutils

import underworld as uw
from underworld import function as fn

# import numpy as np
# from planetengine.utilities import Grouper
# from planetengine.observer import ObsVar

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

from planetengine.newstats import ScalarIntegral

class VarUtils:

    def __init__(
            self,
            inVar,
            recursions = 2,
            attach = True,
            pemesh = None,
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

        planetengine.message("Initialising VarUtils...")

        stInp = planetengine.standards.standardise(inVar, heavy = True)
        self.stInp = stInp
        self.__dict__.update(stInp.__dict__)

        self.attach = attach
        self.recursions = recursions

        if self.attach == True and hasattr(self.var, 'pe_varUtils'):
            raise Exception("Var already has 'pe' attribute: aborting.")

        if not self.varType == 'special':

            if pemesh is None:
                try:
                    self.pemesh = meshutils.MeshUtils(self.mesh)
                except:
                    self.pemesh = self.mesh.pe
            else:
                self.pemesh = pemesh

            self._add_stats()

            if self.recursions > 0:
                self._recursion()

        if self.attach:
            planetengine.message("Attaching...")
            self.var.__dict__.update({'pe_varUtils': self})
            planetengine.message("Done!")

    def _add_stats(self):

        planetengine.message("Adding stats...")

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
                        self.pemesh.comps.keys()
            elif self.dim == self.mesh.dim:
                if self.recursions == 0:
                    scalarIntegralSuite['surface'] = \
                        ['volume', 'inner', 'outer']
                    scalarIntegralSuite['comp'] = \
                        ['mag']
                    scalarIntegralSuite['comp'] += \
                        self.pemesh.comps.keys()

            for inputDict in utilities.suite_list(scalarIntegralSuite):
                anVar = ScalarIntegral(
                    self.stInp,
                    **inputDict
                    )
                self.statsDict[anVar.opTag] = anVar

            else:
                pass

        else:
            pass

        self.__dict__.update(self.statsDict)

    def _recursion(self):

        planetengine.message("Adding recursions...")

        new_recursions = self.recursions - 1

        # Define all the recursion functions:

        recursionFuncs = {}

        if self.dim == 1:
            recursionFuncs['radGrad'] = fn.math.dot(
                self.pemesh.rad,
                self.gradient
                )
            recursionFuncs['magGrad'] = fn.math.sqrt(
                fn.math.dot(
                    self.gradient,
                    self.gradient
                    )
                )
            if self.mesh.dim == 2:
                recursionFuncs['angGrad'] = fn.math.dot(
                    self.pemesh.ang,
                    self.gradient
                    )
            elif self.mesh.dim == 3:
                recursionFuncs['angGrad1'] = fn.math.dot(
                    self.pemesh.ang1,
                    self.gradient
                    )
                recursionFuncs['angGrad2'] = fn.math.dot(
                    self.pemesh.ang1,
                    self.gradient
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
                self.pemesh.rad,
                self.meshVar
                )

            if self.dim == 2:

                recursionFuncs['angComp'] = fn.math.dot(
                    self.pemesh.ang,
                    self.meshVar
                    )

            elif self.dim == 3:

                recursionFuncs['angComp1'] = fn.math.dot(
                    self.pemesh.ang1,
                    self.meshVar
                    )
                recursionFuncs['angComp2'] = fn.math.dot(
                    self.pemesh.ang2,
                    self.meshVar
                    )

            else:
                raise Exception(
                    "Dimensions greater than three not yet supported."
                    )

        # Now use the recursion funcs to build VarUtils
        # and make them attributes of the parent VarUtils:

        for varName, var in sorted(recursionFuncs.items()):

            newStInp = planetengine.standards.StandardInput(
                (varName, var, self.mesh),
                inheritedUpdate = self.update,
                heavy = True
                )
            newVar = VarUtils(
                newStInp,
                recursions = new_recursions,
                inheritedUpdate = self.update
                )

            setattr(self, varName, newVar)

        # Done!

        planetengine.message("Added recursions.")
