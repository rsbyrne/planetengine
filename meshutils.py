from .utilities import get_scales

import underworld as uw
from underworld import function as fn

import numpy as np

def get_meshUtils(mesh):
    meshUtils = MeshUtils(mesh)
    return meshUtils

class MeshUtils:

    def __init__(
            self,
            mesh,
            ):

        if type(mesh) == uw.mesh.FeMesh_Cartesian:

            self.surfaces = {
                'inner': mesh.specialSets['Bottom_VertexSet'],
                'outer': mesh.specialSets['Top_VertexSet'],
                'left': mesh.specialSets['Left_VertexSet'],
                'right': mesh.specialSets['Right_VertexSet']
                }
            if mesh.dim == 2:
                self.comps = {
                    'ang': fn.misc.constant((1., 0.)),
                    'rad': fn.misc.constant((0., -1.)),
                    }
            elif mesh.dim == 3:
                self.comps = {
                    'ang1': fn.misc.constant((1., 0., 0.)),
                    'ang2': fn.misc.constant((0., 1., 0.)),
                    'rad': fn.misc.constant((0., 0., -1.)),
                    }
                self.surfaces['front'] = mesh.specialSets['MinK_VertexSet']
                self.surfaces['back'] = mesh.specialSets['MaxK_VertexSet']
        elif type(mesh) == uw.mesh.FeMesh_Annulus:
            self.comps = {
                'ang': mesh.unitvec_theta_Fn,
                'rad': -mesh.unitvec_r_Fn,
                }
            self.surfaces = {
                'inner': mesh.specialSets['inner'],
                'outer': mesh.specialSets['outer'],
                'left': mesh.specialSets['MaxJ_VertexSet'],
                'right': mesh.specialSets['MinJ_VertexSet']
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
