# from . import utilities
# from . import mapping
# from . import projection
# from . import meshutils

# import underworld as uw
# from underworld import function as fn

# import numpy as np

# from mpi4py import MPI
# comm = MPI.COMM_WORLD
# rank = comm.Get_rank()
# nProcs = comm.Get_size()

# ignoreVal = 1e18 * 0.4431257522991823 + 0.9913948956024117



# def get_meshUtils(

# # def get_meshUtils(
# #         mesh,
# #         attach = True,
# #         deformable = False,
# #         ):

# #     if hasattr(mesh, 'meshUtils'):
# #         meshUtils = mesh.meshUtils
# #     else:
# #         meshUtils = meshUtils(
# #             mesh,
# #             deformable
# #             )
# #         if attach:
# #             setattr(mesh, 'meshUtils', meshUtils)

# #     return meshUtils

# # default_mesh = {
# #     2: uw.mesh.FeMesh_Cartesian(
# #         elementRes = [64, 64],
# #         minCoord = [0., 0.],
# #         maxCoord = [1., 1.]
# #         ),
# #     3: uw.mesh.FeMesh_Cartesian(
# #         elementRes = [64, 64, 64],
# #         minCoord = [0., 0., 0.],
# #         maxCoord = [1., 1., 1.]
# #         )
# #     }

# # def make_pevar(var, attach = True, force = False):

# #     if type(var) is PeVar:
# #         pevar = var
# # #         planetengine.message("Input is already a PeVar.")
# #     elif hasattr(var, 'pevar') and not force:
# #         assert type(var.pevar) is PeVar
# #         pevar = var.pevar
# # #         planetengine.message(
# # #             "Input already has a PeVar. \
# # #             To force creation of a new one, \
# # #             set the 'force' kwarg = True."
# # #             )
# #     else:
# #         unpacked = utilities.unpack_var(var)
# #         var = unpacked[0]
# #         pevar = PeVar(unpacked)
# #         if attach:
# #             setattr(var, 'pevar', pevar)
# #     pevar.update()
# #     return pevar

# # def make_pemesh(
# #         mesh,
# #         attach = True,
# #         deformable = False,
# #         ):

# #     if hasattr(mesh, 'pemesh'):
# #         pemesh = mesh.pemesh
# #     else:
# #         pemesh = PeMesh(
# #             mesh,
# #             deformable
# #             )
# #         if attach:
# #             setattr(mesh, 'pemesh', pemesh)

# #     return pemesh

# # def standardise(var, attach = True):
# #     try: stVar = make_pevar(var, attach)
# #     except: stVar = make_pemesh(var, attach)
# #     return stVar

# # class PeVar:
    
# #     def __init__(
# #             self,
# #             unpackedVar
# #             ):

# #         self.var = unpackedVar[0]
# #         self.varType = unpackedVar[1]
# #         self.mesh = unpackedVar[2]
# #         self.substrate = unpackedVar[3]
# #         self.dType = unpackedVar[4]
# #         self.varDim = unpackedVar[5]

# #         self.vector = self.varDim == self.mesh.dim
# #         assert self.vector or self.varDim == 1
# #         self.discrete = self.dType == 'int'
# #         self.boolean = self.dType == 'boolean'
# #         self.particles = self.varType in ('swarmVar', 'swarmFn')

# #         self.pemesh = make_pemesh(self.mesh)

# #         if self.varType == 'meshVar':
# #             self.meshVar = self.var
# #         else:
# #             self.meshVar = utilities.make_projector(
# #                 self.var, self.substrate
# #                 )
# #             self.meshVar.project()
# #         self.valSets = utilities.get_valSets(self.meshVar)

# #     def update(self):
# #         if hasattr(self.meshVar, 'project'):
# #             self.meshVar.project()
# #         self.pemesh.update()
# #         self.valSets = utilities.get_valSets(self.meshVar)

# # class PeMesh:

# #     def __init__(
# #             self,
# #             mesh,
# #             deformable = False,
# #             ):

# #         self.mesh = mesh
# #         self.deformable = deformable
# #         self.updateFuncs = []

# #         self.var1D = mesh.add_variable(nodeDofCount = 1)
# #         self.var2D = mesh.add_variable(nodeDofCount = 2)
# #         self.var3D = mesh.add_variable(nodeDofCount = 3)

# #         self.autoVars = {
# #             1: self.var1D,
# #             2: self.var2D,
# #             3: self.var3D,
# #             }

# #         if type(self.mesh) == uw.mesh.FeMesh_Cartesian:
# #             self.surfaces = {
# #                 'inner': mesh.specialSets['Bottom_VertexSet'],
# #                 'outer': mesh.specialSets['Top_VertexSet'],
# #                 'left': mesh.specialSets['Left_VertexSet'],
# #                 'right': mesh.specialSets['Right_VertexSet']
# #                 }
# #             if self.mesh.dim == 2:
# #                 self.comps = {
# #                     'ang': fn.misc.constant((1., 0.)),
# #                     'rad': fn.misc.constant((0., -1.)),
# #                     }
# #             elif mesh.dim == 3:
# #                 self.comps = {
# #                     'ang1': fn.misc.constant((1., 0., 0.)),
# #                     'ang2': fn.misc.constant((0., 1., 0.)),
# #                     'rad': fn.misc.constant((0., 0., -1.)),
# #                     }
# #                 self.surfaces['front'] = mesh.specialSets['MinK_VertexSet']
# #                 self.surfaces['back'] = mesh.specialSets['MaxK_VertexSet']
# #         elif type(mesh) == uw.mesh.FeMesh_Annulus:
# #             self.comps = {
# #                 'ang': mesh.unitvec_theta_Fn,
# #                 'rad': -mesh.unitvec_r_Fn,
# #                 }
# #             self.surfaces = {
# #                 'inner': mesh.specialSets['inner'],
# #                 'outer': mesh.specialSets['outer'],
# #                 'left': mesh.specialSets['MaxJ_VertexSet'],
# #                 'right': mesh.specialSets['MinJ_VertexSet']
# #                 }
# #         else:
# #             raise Exception("That kind of mesh is not supported yet.")

# #         self.wallsList = [
# #             self.surfaces['outer'],
# #             self.surfaces['inner'],
# #             self.surfaces['left'],
# #             self.surfaces['right']
# #             ]
# #         try:
# #             wallsList.append(self.surfaces['front'])
# #             wallsList.append(self.surfaces['back'])
# #         except:
# #             pass

# #         self.__dict__.update(self.comps)
# #         self.__dict__.update(self.surfaces)

# #         self.scales = utilities.get_scales(mesh)

# #         # WEIGHTVARS:
# #         ### THIS IS TOO SLOW ###
# # #         self.weightVar_volume = uw.mesh.MeshVariable(self.mesh, nodeDofCount = 1)
# # #         self.weightVar_outer = uw.mesh.MeshVariable(self.mesh, nodeDofCount = 1)
# # #         self.weightVar_inner = uw.mesh.MeshVariable(self.mesh, nodeDofCount = 1)
# # #         self.weightVars = {
# # #             'volume': self.weightVar_volume,
# # #             'outer': self.weightVar_outer,
# # #             'inner': self.weightVar_inner
# # #             }
# # #         weightVar_maskVar = uw.mesh.MeshVariable(self.mesh, nodeDofCount = 1)
# # #         weightVar_integral_volume = uw.utils.Integral(
# # #             weightVar_maskVar,
# # #             self.mesh
# # #             )
# # #         weightVar_integral_outer = uw.utils.Integral(
# # #             weightVar_maskVar,
# # #             self.mesh,
# # #             integrationType = 'surface',
# # #             surfaceIndexSet = self.outer
# # #             )
# # #         weightVar_integral_inner = uw.utils.Integral(
# # #             weightVar_maskVar,
# # #             self.mesh,
# # #             integrationType = 'surface',
# # #             surfaceIndexSet = self.inner
# # #             )
# # #         weightVarIntegrals = {
# # #             'volume': weightVar_integral_volume,
# # #             'outer': weightVar_integral_outer,
# # #             'inner': weightVar_integral_inner
# # #             }
# # #         def update_weightVars():
# # #             for key, weightVar in sorted(self.weightVars.items()):
# # #                 integral = weightVarIntegrals[key]
# # #                 for index, val in enumerate(weightVar.data):
# # #                     weightVar_maskVar.data[:] = 0.
# # #                     weightVar_maskVar.data[index] = 1.
# # #                     weightVar.data[index] = integral.evaluate()[0]
# # #         update_weightVars()
# # #         self.updateFuncs.append(update_weightVars)

# #         # Is this necessary?
# # #        if not self.deformable:
# # #            fullData = self.getFullData()
# # #            self.fullData = lambda: fullData
# # #        else:
# # #            self.fullData = self.getFullData

# #         # REVISIT THIS WHEN 'BOX' IS IMPROVED
# #         if type(self.mesh) == uw.mesh.FeMesh_Annulus:
# #             if not self.deformable:
# #                 if self.mesh.dim == 2:
# #                     box = mapping.box(self.mesh)
# #                     self.box = lambda: box
# #             else:
# #                 if self.mesh.dim == 2:
# #                     self.box = lambda: mapping.box(self.mesh)
# #             def unbox(coords):
# #                 return mapping.unbox(self.mesh, coords)
# #             self.unbox = unbox

# #         volInt = uw.utils.Integral(
# #             1.,
# #             mesh,
# #             )
# #         outerInt = uw.utils.Integral(
# #             1.,
# #             mesh,
# #             integrationType = 'surface',
# #             surfaceIndexSet = self.outer
# #             )
# #         innerInt = uw.utils.Integral(
# #             1.,
# #             mesh,
# #             integrationType = 'surface',
# #             surfaceIndexSet = self.inner
# #             )

# #         if not deformable:

# #             volIntVal = volInt.evaluate()[0]
# #             outerIntVal = outerInt.evaluate()[0]
# #             innerIntVal = innerInt.evaluate()[0]

# #             self.integral = lambda: volIntVal
# #             self.integral_outer = lambda: outerIntVal
# #             self.integral_inner = lambda: innerIntVal

# #         else:

# #             self.integral = lambda: volInt.evaluate()[0]
# #             self.integral_outer = lambda: outerInt.evaluate()[0]
# #             self.integral_inner = lambda: innerInt.evaluate()[0]

# #         self.integrals = {
# #             'inner': self.integral_inner,
# #             'outer': self.integral_outer,
# #             'volume': self.integral,
# #             }

# #         xs = np.linspace(self.mesh.data[:,0].min(), self.mesh.data[:,0].max(), 100)
# #         ys = np.linspace(self.mesh.data[:,1].min(), self.mesh.data[:,1].max(), 100)
# #         self.cartesianScope = np.array(np.meshgrid(xs, ys)).T.reshape([-1, 2])

# # #    def getFullData(self):
# # #        fullData = fn.input().evaluate_global(self.mesh.data)
# # #        fullData = comm.bcast(fullData, root = 0)
# # #        return fullData

# #         self.meshifieds = {}

# #     def meshify(self, var, return_project = True, rounded = False):

# #         assert not var in self.autoVars.values(), \
# #             "Cannot meshify an already meshified variable!"
# #         if var in self.meshifieds:
# #             projection, projector, inherited_projectors = self.meshifieds[var]
# #         else:
# #             inherited_projectors = []
# #             for subVar in var._underlyingDataItems:
# #                 assert not subVar in self.autoVars.values(), \
# #                     "Variable contains a meshified variable already."
# #                 # see utilities.make_projector:
# #                 try: inherited_projectors.append(subVar.project)
# #                 except: pass
# #             if type(var) == uw.mesh._meshvariable.MeshVariable:
# #                 projection = var
# #                 def project():
# #                     pass
# #             else:
# #                 project = None
# #                 for autoVar in self.autoVars.values():
# #                     try:
# #                         projector = uw.utils.MeshVariable_Projection(
# #                             autoVar,
# #                             var,
# #                             )
# #                         projection = autoVar
# #                         def project():
# #                             for inheritedProj in inherited_projectors:
# #                                 inheritedProj()
# #                             projector.solve()
# #                             if rounded:
# #                                 projection.data[:] = np.round(
# #                                     projection.data
# #                                     )
# #                     except:
# #                         pass
# #                 if project is None:
# #                     raise Exception("Projection failed!")
# #         if return_project:
# #             return projection, project
# #         else:
# #             project()
# #             return projection

# #     def update(self):
# #         if self.deformable:
# #             for updateFunc in self.updateFuncs:
# #                 updateFunc()