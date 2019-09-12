# from .. import mapping
# from ..utilities import get_varInfo
# from ..utilities import get_scales
# from ..fieldops import copyField
# from ..fieldops import set_scales
# from ..fieldops import set_boundaries
# from ..visualisation import quickShow
#
# import underworld as uw
#
# def build(*args, **kwargs):
#     return IC(*args, **kwargs)
#
# class Initials:
#
#     def __init__(
#             self,
#             *args,
#             **kwargs
#             ):
#         self.scripts = [__file__,]
#         ICmodules = *args
#         for ICmodule in ICmodules:
#             for script in ICmodule.script:
#                 self.scripts.append(script)
#
#
#         # initialsDict = kwargs
#
#
#
#
#     def apply(self, varsDict):
#
#         varsOfState = varsDict
#
#         # MAIN LOOP:
#
#         for varName, var in sorted(varsOfState.items()):
#
#             IC = initials[varName]
#             try: boxDims = system.boxDims
#             except: boxDims = ((0., 1.),) * system.mesh.dim
#
#             # APPLY VALUES:
#
#             if type(IC) == load.IC:
#                 tolerance = copyField(
#                     IC.inVar,
#                     var,
#                     )
#
#             else: # hence is an ordinary IC:
#                 if type(var) == uw.mesh.MeshVariable:
#                     box = mapping.box(var.mesh, var.mesh.data, boxDims)
#                 elif type(var) == uw.swarm.SwarmVariable:
#                     box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)
#                 var.data[:] = IC.evaluate(box)
#
#             # APPLY SCALES:
#
#             if hasattr(system, 'varScales'):
#                 if varName in system.varScales:
#                     set_scales(var, system.varScales[varName])
#
#             # APPLY BOUNDARIES:
#
#             if hasattr(system, 'varBounds'):
#                 if varName in system.varBounds:
#                     set_boundaries(var, system.varBounds[varName])
