import planetengine
from planetengine import utilities
from planetengine import mapping

import underworld as uw
from underworld import function as fn

import numpy as np

# from planetengine.utilities import Grouper
# from planetengine.observer import ObsVar

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

class MeshUtils:

    def __init__(
            self,
            mesh,
            meshName = None,
            attach = True,
            deformable = False,
            ):

        self.mesh = mesh
        self.attach = attach
        self.deformable = deformable

        if meshName is None:
            self.meshName = 'noname'
        else:
            self.meshName = meshName

        if self.attach == True and hasattr(self.mesh, 'pe'):
            raise Exception("Mesh already has 'pe' attribute: aborting.")

        self.var1D = mesh.add_variable(nodeDofCount = 1)
        self.var2D = mesh.add_variable(nodeDofCount = 2)
        self.var3D = mesh.add_variable(nodeDofCount = 3)

        self.autoVars = {
            1: self.var1D,
            2: self.var2D,
            3: self.var2D,
            }

        if type(self.mesh) == uw.mesh.FeMesh_Cartesian:
            if self.mesh.dim == 2:
                self.ang = fn.misc.constant((1., 0.))
                self.rad = fn.misc.constant((0., 1.))
            elif mesh.dim == 3:
                self.ang1 = fn.misc.constant((1., 0., 0.))
                self.ang2 = fn.misc.constant((0., 1., 0.))
                self.rad = fn.misc.constant((0., 0., 1.))
            else:
                raise Exception("Only mesh dims 2 and 3 supported...obviously?")
            self.inner = mesh.specialSets['Bottom']
            self.outer = mesh.specialSets['Top']
        elif type(mesh) == uw.mesh.FeMesh_Annulus:
            self.ang = mesh.unitvec_theta_Fn
            self.rad = mesh.unitvec_r_Fn
            self.inner = mesh.specialSets['inner']
            self.outer = mesh.specialSets['outer']
        else:
            raise Exception("That kind of mesh is not supported yet.")

        if mesh.dim == 2:
            self.comps = {
                'ang': self.ang,
                'rad': self.rad,
                }
        else:
            self.comps = {
                'ang1': self.ang1,
                'ang2': self.ang2,
                'rad': self.rad,
                }

        self.surfaces = {
            'inner': self.inner,
            'outer': self.outer,
            }

        # Is this necessary?
#        if not self.deformable:
#            fullData = self.getFullData()
#            self.fullData = lambda: fullData
#        else:
#            self.fullData = self.getFullData

        # REVISIT THIS WHEN 'BOX' IS IMPROVED
        if type(self.mesh) == uw.mesh.FeMesh_Annulus:
            if not self.deformable:
                if self.mesh.dim == 2:
                    box = mapping.box(self.mesh)
                    self.box = lambda: box
            else:
                if self.mesh.dim == 2:
                    self.box = lambda: mapping.box(self.mesh)
            def unbox(coords):
                return mapping.unbox(self.mesh, coords)
            self.unbox = unbox

        volInt = uw.utils.Integral(
            1.,
            mesh,
            )
        outerInt = uw.utils.Integral(
            1.,
            mesh,
            integrationType = 'surface',
            surfaceIndexSet = self.outer
            )
        innerInt = uw.utils.Integral(
            1.,
            mesh,
            integrationType = 'surface',
            surfaceIndexSet = self.inner
            )

        if not deformable:

            volIntVal = volInt.evaluate()[0]
            outerIntVal = outerInt.evaluate()[0]
            innerIntVal = innerInt.evaluate()[0]

            self.integral = lambda: volIntVal
            self.integral_outer = lambda: outerIntVal
            self.integral_inner = lambda: innerIntVal

        else:

            self.integral = lambda: volInt.evaluate()[0]
            self.integral_outer = lambda: outerInt.evaluate()[0]
            self.integral_inner = lambda: innerInt.evaluate()[0]

        self.integrals = {
            'inner': self.integral_inner,
            'outer': self.integral_outer,
            'volume': self.integral,
            }

        xs = np.linspace(self.mesh.data[:,0].min(), self.mesh.data[:,0].max(), 100)
        ys = np.linspace(self.mesh.data[:,1].min(), self.mesh.data[:,1].max(), 100)
        self.cartesianScope = np.array(np.meshgrid(xs, ys)).T.reshape([-1, 2])

        if self.attach:
            if rank == 0:
                print("Attaching...")
            self.mesh.__dict__.update({'pe_meshUtils': self})
            if rank == 0:
                print("Done!")

#    def getFullData(self):
#        fullData = fn.input().evaluate_global(self.mesh.data)
#        fullData = comm.bcast(fullData, root = 0)
#        return fullData

    def meshify(self, var):

        for autoVar in self.autoVars.values():
            try:
                projector = uw.utils.MeshVariable_Projection(
                    autoVar,
                    var,
                    )
                projector.solve()
                return autoVar, projector
            except:
                pass
        raise Exception("Projection failed!")
