import planetengine.initials.sinusoidal
import planetengine.initials.extents
import planetengine.initials.load
from planetengine import mapping
from planetengine.utilities import unpack_var
from planetengine.utilities import copyField

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    walls = planetengine.standardise(mesh).wallsList

    for i, component in enumerate(values):
        for value, wall in zip(component, walls):
            if not value is '.':
                variable.data[wall, i] = value

def set_scales(variable, values):

    variable.data[:] = mapping.rescale_array(
        variable.data,
        mapping.get_scales(variable),
        values
        )

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
        var, varType, mesh, substrate, data, dType, varDim = unpack_var(var)
        try: boxDims = system.boxDims
        except: boxDims = ((0., 1.),) * system.mesh.dim

        # APPLY VALUES:

        if hasattr(IC, 'LOADTYPE'):
            tolerance = copyField(IC.inVar, var)

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

def preview(IC, _2D = True):
    if hasattr(IC, 'LOADTYPE'):
        var, varType, mesh, substrate, data, dType, varDim = \
            planetengine.unpack_var(IC.inVar)
        pemesh = planetengine.standards.default_mesh[mesh.dim]
        standinVar = pemesh.autoVars[varDim]
        planetengine.copyField(var, standinVar)
    else:
        try:
            pemesh = planetengine.standards.default_mesh[2]
            preview_data = IC.evaluate(pemesh.mesh.data)
        except:
            pemesh = planetengine.standards.default_mesh[3]
            preview_data = IC.evaluate(pemesh.mesh.data)
        standinVar = pemesh.autoVars[preview_data.shape[1]]
        standinVar.data[:] = preview_data
    planetengine.quickShow(standinVar)
