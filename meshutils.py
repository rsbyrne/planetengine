from .utilities import get_scales
from .utilities import get_mesh

import underworld as uw
from underworld import function as _fn

import numpy as np
import weakref

def get_meshUtils(var):
    try:
        mesh = var
        if not hasattr(mesh, 'meshUtils'):
            # POTENTIAL CIRCULAR REFERENCE
            mesh.meshUtils = MeshUtils(mesh)
        return mesh.meshUtils
    except:
        mesh = get_mesh(var)
        return get_meshUtils(mesh)

class MeshUtils:

    def __init__(
            self,
            mesh,
            ):

        if type(mesh) == uw.mesh.FeMesh_Cartesian:

            self.flip = [False, False]

            self.surfaces = {
                'inner': mesh.specialSets['Bottom_VertexSet'],
                'outer': mesh.specialSets['Top_VertexSet'],
                'left': mesh.specialSets['Left_VertexSet'],
                'right': mesh.specialSets['Right_VertexSet'],
                'all': mesh.specialSets['AllWalls_VertexSet']
                }
            if mesh.dim == 2:
                self.comps = {
                    'x': _fn.misc.constant((1., 0.)),
                    'y': _fn.misc.constant((0., 1.)),
                    'ang': _fn.misc.constant((1., 0.)),
                    'rad': _fn.misc.constant((0., -1.)),
                    }
            elif mesh.dim == 3:
                self.comps = {
                    'x': _fn.misc.constant((1., 0., 0.)),
                    'y': _fn.misc.constant((0., 1., 0.)),
                    'z': _fn.misc.constant((0., 0., 1.)),
                    'ang': _fn.misc.constant((1., 0., 0.)),
                    'coang': _fn.misc.constant((0., 1., 0.)),
                    'rad': _fn.misc.constant((0., 0., -1.)),
                    }
                self.surfaces['front'] = mesh.specialSets['MinK_VertexSet']
                self.surfaces['back'] = mesh.specialSets['MaxK_VertexSet']
        elif type(mesh) == uw.mesh.FeMesh_Annulus:

            ### DEBUGGING ###
            # self.flip = [True, False]
            self.flip = [True, True]

            self.comps = {
                'x': _fn.misc.constant((1., 0.)),
                'y': _fn.misc.constant((0., 1.)),
                'ang': -mesh.unitvec_theta_Fn, # left to right
                'rad': mesh.unitvec_r_Fn, # bottom to top
                }
            self.surfaces = {
                'inner': mesh.specialSets['inner'],
                'outer': mesh.specialSets['outer'],
                'left': mesh.specialSets['MaxJ_VertexSet'],
                'right': mesh.specialSets['MinJ_VertexSet'],
                'all': mesh.specialSets['AllWalls_VertexSet']
                }
        else:
            raise Exception("That kind of mesh is not supported yet.")

        self.wallsList = [
            self.surfaces['outer'],
            self.surfaces['inner'],
            self.surfaces['left'],
            self.surfaces['right']
            ]
        try:
            wallsList.append(self.surfaces['front'])
            wallsList.append(self.surfaces['back'])
        except:
            pass

        self.__dict__.update(self.comps)
        self.__dict__.update(self.surfaces)

        self.scales = get_scales(mesh.data)

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

        deformable = False # CHANGE WHEN DEFORMABLE MESHES SUPPORTED
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

        xs = np.linspace(mesh.data[:,0].min(), mesh.data[:,0].max(), 100)
        ys = np.linspace(mesh.data[:,1].min(), mesh.data[:,1].max(), 100)
        self.cartesianScope = np.array(np.meshgrid(xs, ys)).T.reshape([-1, 2])

        self.mesh = weakref.ref(mesh)

    def get_unitVar(self):
        if not hasattr(self, 'unitVar'):
            self.unitVar = self.mesh().add_variable(1)
            self.unitVar.data[:] = 1.
        return self.unitVar

    # def meshify(self, inVar, vector = False):
    #     if not vector:
    #         projector = self.get_scalarProjector()
    #
    #
    # def get_scalarProjector(self):
    #     if not hasattr(self, 'scalarProjector'):
    #         self._make_scalarProjector()
    #     return self.scalarProjector
    #
    # def get_vectorProjector(self):
    #     if not hasattr(self, 'vectorProjector'):
    #         self._make_vectorProjector()
    #     return self.vectorProjector
    #
    # def _make_scalarProjector(self):
    #     fromVar = self._make_scalarVar()
    #     toVar = self._make_scalarVar()
    #     projector = uw.utils.MeshVariable_Projection(
    #         toVar,
    #         fromVar,
    #         )
    #     self.scalarProjector = projector
    #
    # def _make_vectorProjector(self):
    #     fromVar = self._make_vectorVar()
    #     toVar = self._make_vectorVar()
    #     projector = uw.utils.MeshVariable_Projection(
    #         toVar,
    #         fromVar,
    #         )
    #     self.vectorProjector = projector
    #
    # def _make_scalarVar(self):
    #     return self.mesh().add_variable(1)
    #
    # def _make_vectorVar(self):
    #     return self.mesh().add_variable(self.mesh().dim)
