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

        initial = initials[varName]
        IC = initial['IC']
        var, varType, mesh, substrate, data, dType, varDim = unpack_var(var)
        try: boxDims = initial['boxDims']
        except: boxDims = ((0., 1.),) * system.mesh.dim

        # APPLY VALUES:

        if hasattr(IC, 'LOADTYPE'):
            tolerance = copyField(IC.inVar, var)

        else: # hence is an ordinary IC:
            box = mapping.box(mesh, substrate.data, boxDims)
            var.data[:] = IC.evaluate(box)

        # APPLY SCALES:

        if 'varScales' in initial:
            set_scales(var, initial['varScales'])

        # APPLY BOUNDARIES:

        if 'varBounds' in initial:
            set_boundaries(var, initial['varBounds'])

    # RESET PROGRESS VARS:

    system.step.value = 0
    system.modeltime.value = 0.

def preview(IC, _2D = True):
    if hasattr(IC, 'LOADTYPE'):
        var, varType, mesh, substrate, data, dType, varDim = \
            planetengine.unpack_var(IC.inVar)
        if mesh.dim == 2:
            pemesh = planetengine.standardise(
                planetengine.standards.default_mesh_2D
                )
        else:
            pemesh = planetengine.standardise(
                planetengine.standards.default_mesh_3D
                )
        standinVar = pemesh.autoVars[varDim]
        planetengine.copyField(var, standinVar)
    else:
        try:
            pemesh = planetengine.standardise(
                planetengine.standards.default_mesh_2D
                )
            preview_data = IC.evaluate(pemesh.mesh.data)
        except:
            pemesh = planetengine.standardise(
                planetengine.standards.default_mesh_3D
                )
            preview_data = IC.evaluate(pemesh.mesh.data)
        standinVar = pemesh.autoVars[preview_data.shape[1]]
        standinVar.data[:] = preview_data
    planetengine.quickShow(standinVar)
