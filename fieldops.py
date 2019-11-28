import numpy as np
import weakref

import underworld as uw
from underworld import function as _fn

from .meshutils import get_meshUtils
from . import mapping
from . import utilities
from .functions import projection as _projection
get_scales = utilities.get_scales
message = utilities.message

from . import mpi

fullLocalMeshVars = {}

def get_global_var_data(var, subMesh = False):
    substrate = utilities.get_prioritySubstrate(var)
    if subMesh:
        substrate = substrate.subMesh
    if isinstance(var, _fn._function.Function):
        varData = var.evaluate(substrate)
    else:
        varData = var.data
    nodegId = substrate.data_nodegId
    sortNodes = [
        int(node) for node in nodegId
        ]
    data = utilities.globalise_array(
        varData,
        sortNodes
        )
    return data

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    if not hasattr(variable, 'data'):
        raise Exception("Variable lacks 'data' attribute.")

    meshUtils = get_meshUtils(variable.mesh)
    walls = meshUtils.wallsList

    if values is None:
        try:
            values = variable.bounds
        except:
            raise Exception

    for i, component in enumerate(values):
        for value, wall in zip(component, walls):
            if not value in ['.', '!']:
                variable.data[wall, i] = value

def try_set_boundaries(variable, variable2 = None):
    if variable2 is None:
        try:
            set_boundaries(variable)
        except:
            pass
    else:
        try:
            set_boundaries(variable, variable2.boundaries)
        except:
            pass

def set_scales(variable, values = None):

    if not hasattr(variable, 'data'):
        raise Exception("Variable lacks 'data' attribute.")

    if values is None:
        try:
            values = variable.scales
        except:
            raise Exception

    variable.data[:] = mapping.rescale_array(
        variable.data,
        get_scales(variable.data),
        values
        )

def try_set_scales(variable, variable2 = None):
    if variable2 is None:
        try:
            set_scales(variable)
        except:
            pass
    else:
        try:
            set_scales(variable, variable2.scales)
        except:
            pass

def normalise(variable, norm = [0., 1.]):
    scales = [
        norm \
            for dim in range(
                variable.data.shape[1]
                )
        ]
    set_scales(variable, scales)

def clip_array(variable, scales):
    variable.data[:] = np.array([
        np.clip(subarr, *clipval) \
            for subarr, clipval in zip(
                variable.data.T,
                scales
                )
        ]).T

def copyField(fromField, toField, maxTolerance = 0.01):
    # NOT KNOWN TO BE PARALLEL SAFE YET
    if not hasattr(fromField, 'evaluate'):
        raise Exception
    if not type(toField) == uw.mesh._meshvariable.MeshVariable:
        raise Exception
    toMesh = utilities.get_mesh(toField)
    toBox = mapping.box(toMesh)
    outArray, tolerance = mapping.safe_box_evaluate(
        fromField,
        toBox,
        maxTolerance
        )
    toField.data[...] = outArray
    return tolerance
