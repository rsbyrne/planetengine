import planetengine.initials.sinusoidal
import planetengine.initials.extents
import planetengine.initials.load
from planetengine import mapping
from planetengine.meshutils import mesh_utils
from planetengine.standards import basic_unpack

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    pemesh = mesh_utils(mesh)

    for value, wall in zip(values, pemesh.surfaces):
        if not value is '.':
            variable.data[wall] = value

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
        ignore, var, mesh, swarm, coords, data, dType = basic_unpack(var)
        try: boxDims = initial['boxDims']
        except: boxDims = ((0., 1.),) * system.mesh.dim

        # APPLY VALUES:

        if hasattr(IC, 'LOADTYPE'):
            tolerance = copyField(IC.inVar, var)

        else: # hence is an ordinary IC:
            box = mapping.box(mesh, coords, boxDims)
            var.data[:] = IC.evaluate(box)

        # APPLY SCALES:

        if 'varScales' in initial:
            varScale = initial['varScales']
            mapping.rescale_array(
                var.data,
                mapping.get_scales(var),
                varScale
                )

        # APPLY BOUNDARIES:

        if 'varBounds' in initial:
            varBounds = initial['varBounds']
            set_boundaries(var, varBounds)

    # RESET PROGRESS VARS:

    system.step.value = 0
    system.modeltime.value = 0.