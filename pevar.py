import underworld as uw
from underworld import function as fn
import planetengine
import numpy as np

def make_pevar(var, attach = True):

    if type(var) is PeVar:
        pevar = var
    elif hasattr(var, 'pevar'):
        assert type(var.pevar) is PeVar
        pevar = var.pevar
    else:
        unpacked = planetengine.utilities.unpack_var(var)
        var = unpacked[0]
        pevar = PeVar(unpacked)
        if attach:
            setattr(var, 'pevar', pevar)
    return pevar

class PeVar:
    
    def __init__(
            self,
            unpackedVar
            ):

        self.var = unpackedVar[0]
        self.varType = unpackedVar[1]
        self.mesh = unpackedVar[2]
        self.substrate = unpackedVar[3]
        self.data = unpackedVar[4]
        self.dType = unpackedVar[5]
        self.varDim = unpackedVar[6]

        self.vector = self.varDim == self.mesh.dim
        self.discrete = self.dType == 'int'
        self.boolean = self.dType == 'boolean'
        self.particles = self.varType in ('swarmVar', 'swarmFn')

        self.isPevar = True

        self.meshUtils = planetengine.meshutils.mesh_utils(self.mesh)

        if not self.varType == 'meshVar':
            self.projection = planetengine.utilities.make_projector(
                self.var, self.substrate
                )

    def meshVar(self, update = True):
        if self.varType == 'meshVar':
            if hasattr(self.var, 'project'):
                if update:
                    self.var.project()
            return self.var
        else:
            if update:
                self.projection.project()
            return self.projection

# def standardise(
#         *args,
#         attach = True,
#         heavy = True,
#         inheritedUpdate = None
#         ):

#     stInp = None

#     if len(args) == 1 and type(args[0]) == tuple:
#         args = args[0]
#     inputTypes = {type(arg): arg for arg in args}
#     if StandardInput in inputTypes:
#         stInp = inputTypes[StandardInput]
#     else:
#         for arg in args:
#             if hasattr(arg, 'pe_stInp'):
#                 stInp = arg.pe_stInp
#     if stInp == None:
#         varName = 'noname'
#         substrate = None
#         if len(args) == 1:
#             var = args[0]
#         elif len(args) == 2:
#             if type(args[0]) == str:
#                 varName, var = args
#             else:
#                 var, substrate = args
#         elif len(args) == 3:
#             varName, var, substrate = args
#         else:
#             raise Exception("Input not understood.")
#         stInp = StandardInput(
#             var,
#             varName,
#             substrate,
#             heavy = heavy,
#             inheritedUpdate = inheritedUpdate
#             )
#     if attach:
#         if not hasattr(stInp.var, 'pe_stInp'):
#             stInp.var.__dict__.update({'pe_stInp': stInp})
#     return stInp

# class StandardInput:

#     def __init__(
#             self,
#             var,
#             varName,
#             substrate,
#             inheritedUpdate = None,
#             heavy = True,
#             ):

#         self.heavy = heavy
#         self.inheritedUpdate = inheritedUpdate
#         self.var = var
#         self.substrate = substrate
#         self.varName = varName
#         if not self.substrate is None: # hence var is a function:
#             self.dim = self.var.evaluate(self.substrate).shape[1]
#             try:
#                 self.substrateName = 'swarm'
#                 self.swarm = self.substrate
#                 self.mesh = self.swarm.mesh
#                 self.varType = 'swarmFn'
#                 self.types = {'swarm', 'function'}
#             except:
#                 self.substrateName = 'mesh'
#                 self.swarm = None
#                 self.mesh = self.substrate
#                 self.varType = 'meshFn'
#                 self.types = {'mesh', 'function'}
#         elif type(self.var) == uw.mesh._meshvariable.MeshVariable:
#             self.substrateName = 'mesh'
#             self.dim = self.var.nodeDofCount
#             self.substrate = self.var.mesh
#             self.swarm = None
#             self.mesh = self.var.mesh
#             self.varType = 'meshVar'
#             self.types = {'mesh', 'variable'}
#         elif type(self.var) == uw.swarm._swarmvariable.SwarmVariable:
#             self.substrateName = 'swarm'
#             self.dim = self.var.count
#             self.substrate = self.var.swarm
#             self.swarm = self.substrate
#             self.mesh = self.swarm.mesh
#             self.varType = 'swarmVar'
#             self.types = {'swarm', 'variable'}
#         else:
#             raise Exception("Input not recognised.")

#         if self.dim == 1:
#             self.types.add('scalar')
#         elif self.dim == self.mesh.dim:
#             self.types.add('vector')
#         else:
#             raise Exception(
#                 "Only scalars and spatially-referenced vectors accepted."
#                 )

#         self.pemesh = planetengine.meshutils.mesh_utils(self.mesh)

#         if not self.varType in {'mesh', 'swarm'}:
#             if self.varType == 'meshVar':
#                 def meshVar():
#                     if not self.inheritedUpdate is None:
#                         self.inheritedUpdate()
#                     return self.var
#                 self.meshVar = lambda: self.var
#             elif self.heavy:
#                 projection, project = planetengine.utilities.make_projector(
#                     self.var, self.substrate
#                     )
#                 def meshVar():
#                     project()
#                     return projection
#                 self.meshVar = meshVar
#             else:
#                 self.meshVar = self.pemesh.meshify(
#                     self.var,
#                     self.inheritedUpdate
#                     )
#             self.gradient = self.meshVar().fn_gradient

#         def data():
#             return self.meshVar().data
#         self.data = data

#         dataSnapshot = data()
#         if str(dataSnapshot.dtype) == 'int32':
#             self.dType = 'int'
#             self.types.add('discrete')
#             if 0 in dataSnapshot:
#                 self.types.add('binary')
#         elif str(dataSnapshot.dtype) == 'float64':
#             self.dType = 'double'
#             self.types.add('continuous')
#         elif str(dataSnapshot.dtype) == 'bool':
#             self.dType = 'boolean'
#             self.types.add('discrete')
#             self.types.add('binary')
#         else:
#             raise Exception(
#                 "Input data type not acceptable."
#                 )