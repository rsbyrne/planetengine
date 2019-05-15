import planetengine
from planetengine import utilities
from planetengine import mapping
from planetengine.standards import basic_unpack

import underworld as uw
from underworld import function as fn

import numpy as np

# from planetengine.utilities import Grouper
# from planetengine.observer import ObsVar

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

def mesh_utils(
        mesh,
        meshName = None,
        attach = True,
        deformable = False,
        ):

    if hasattr(mesh, 'pe'):
        pe = mesh.pe
    else:
        pe = MeshUtils(*args, **kwargs)

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
            self.surfaces = {
                'inner': mesh.specialSets['MinJ_VertexSet'],
                'outer': mesh.specialSets['MaxJ_VertexSet'],
                'left': mesh.specialSets['MinI_VertexSet'],
                'right': mesh.specialSets['MaxI_VertexSet']
                }
            if self.mesh.dim == 2:
                self.comps = {
                    'ang': fn.misc.constant((1., 0.)),
                    'rad': fn.misc.constant((0., 1.)),
                    }
            elif mesh.dim == 3:
                self.comps = {
                    'ang1': fn.misc.constant((1., 0., 0.)),
                    'ang2': fn.misc.constant((0., 1., 0.)),
                    'rad': fn.misc.constant((0., 0., 1.)),
                    }
                self.surfaces['front'] = mesh.specialSets['MinK_VertexSet']
                self.surfaces['back'] = mesh.specialSets['MaxK_VertexSet']
        elif type(mesh) == uw.mesh.FeMesh_Annulus:
            self.comps = {
                'ang': mesh.unitvec_theta_Fn,
                'rad': mesh.unitvec_r_Fn,
                }
            self.surfaces = {
                'inner': mesh.specialSets['inner'],
                'outer': mesh.specialSets['outer'],
                'left': mesh.specialSets['MinJ_VertexSet'],
                'right': mesh.specialSets['MaxJ_VertexSet']
                }
        else:
            raise Exception("That kind of mesh is not supported yet.")

        self.__dict__.update(self.comps)
        self.__dict__.update(self.surfaces)

        self.scales = mapping.get_scales(mesh, partitioned = True)

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
            self.mesh.__dict__.update({'pe': self})
            if rank == 0:
                print("Done!")

#    def getFullData(self):
#        fullData = fn.input().evaluate_global(self.mesh.data)
#        fullData = comm.bcast(fullData, root = 0)
#        return fullData

    def meshify(self, var, return_func = True):

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            planetengine.message(
                "Already a mesh var..."
                )
            if return_func:
                def meshVar():
                    return var
            else:
                return meshVar, None
        else:
            for autoVar in self.autoVars.values():
                try:
                    projector = uw.utils.MeshVariable_Projection(
                        autoVar,
                        var,
                        )
                    projector.solve()
                    if return_func:
                        def meshVar():
                            projector.solve()
                            return autoVar
                        return meshVar
                    else:
                        return autoVar, projector
                except:
                    pass
        raise Exception("Projection failed!")
