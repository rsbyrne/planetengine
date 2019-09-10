from . import sinusoidal
from . import extents
from . import load

from .. import mapping
from ..utilities import get_varInfo
from ..utilities import get_scales
from ..fieldops import copyField
from ..fieldops import set_scales
from ..fieldops import set_boundaries
from ..visualisation import quickShow

import underworld as uw

def apply(initials, system):

    varsOfState = system.varsOfState

    # MAIN LOOP:

    for varName, var in sorted(varsOfState.items()):

        IC = initials[varName]
        try: boxDims = system.boxDims
        except: boxDims = ((0., 1.),) * system.mesh.dim

        # APPLY VALUES:

        if type(IC) == load.IC:
            tolerance = copyField(
                IC.inVar,
                var,
                )

        else: # hence is an ordinary IC:
            if type(var) == uw.mesh.MeshVariable:
                box = mapping.box(var.mesh, var.mesh.data, boxDims)
            elif type(var) == uw.swarm.SwarmVariable:
                box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)
            var.data[:] = IC.evaluate(box)

        # APPLY SCALES:

        if hasattr(system, 'varScales'):
            if varName in system.varScales:
                set_scales(var, system.varScales[varName])

        # APPLY BOUNDARIES:

        if hasattr(system, 'varBounds'):
            if varName in system.varBounds:
                set_boundaries(var, system.varBounds[varName])

    # RESET PROGRESS VARS:

    # system.step.value = 0
    # system.modeltime.value = 0.

# def preview(IC, _2D = True):
#     if hasattr(IC, 'LOADTYPE'):
#         var, varType, mesh, substrate, dType, varDim = \
#             get_varInfo(IC.inVar)
#         pemesh = standards.default_mesh[mesh.dim]
#         standinVar = pemesh.autoVars[varDim]
#         copyField(var, standinVar)
#     else:
#         try:
#             pemesh = standards.default_mesh[2]
#             preview_data = IC.evaluate(pemesh.mesh.data)
#         except:
#             pemesh = standards.default_mesh[3]
#             preview_data = IC.evaluate(pemesh.mesh.data)
#         standinVar = pemesh.autoVars[preview_data.shape[1]]
#         standinVar.data[:] = preview_data
#     quickShow(standinVar)
