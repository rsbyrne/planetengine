from . import sinusoidal
from . import extents
from . import load

from .. import mapping
from ..utilities import unpack_var
from ..utilities import get_scales
from ..fieldops import copyField
from ..fieldops import set_scales
from ..fieldops import set_boundaries
from ..visualisation import quickShow

def apply(initials, system):

    if hasattr(system, "sub_systems"):
        for sub_system in inputs.sub_systems:
            apply(initials, sub_system)
    else:
        _apply(initials, system)

def _apply(initials, system):

    varsOfState = system.varsOfState

    # MAIN LOOP:

    for varName, var in sorted(varsOfState.items()):

        IC = initials[varName]
        var, varType, mesh, substrate, dType, varDim = unpack_var(var)
        try: boxDims = system.boxDims
        except: boxDims = ((0., 1.),) * system.mesh.dim

        # APPLY VALUES:

        if hasattr(IC, 'LOADTYPE'):
            tolerance = copyField(
                IC.inVar,
                var,
                )

        else: # hence is an ordinary IC:
            box = mapping.box(mesh, substrate.data, boxDims)
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

    system.step.value = 0
    system.modeltime.value = 0.

# def preview(IC, _2D = True):
#     if hasattr(IC, 'LOADTYPE'):
#         var, varType, mesh, substrate, dType, varDim = \
#             unpack_var(IC.inVar)
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