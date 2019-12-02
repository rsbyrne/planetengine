import numpy as np
import scipy as sp
import weakref

import underworld as uw
from underworld import function as fn

from .meshutils import get_meshUtils
from . import mapping
from . import utilities
from . import mpi
from . import exceptions
message = utilities.message

def get_global_var_data(var, subMesh = False):
    substrate = utilities.get_prioritySubstrate(var)
    if subMesh:
        substrate = substrate.subMesh
    if isinstance(var,fn._function.Function):
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
        utilities.get_scales(variable.data),
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

def box_evaluate(
        var,
        boxCoords,
        tolerance = 0.,
        fromMesh = None,
        globalFromMesh = None,
        globalFromField = None,
        checkNaN = True
        ):
    if fromMesh is None:
        fromMesh = utilities.get_mesh(var)
    if globalFromMesh is None:
        globalFromMesh = get_global_var_data(fromMesh)
    if globalFromField is None:
        globalFromField = get_global_var_data(var)
    evalCoords = mapping.unbox(
        fromMesh,
        boxCoords,
        tolerance = tolerance,
        shrinkLocal = True
        )
    data = sp.interpolate.griddata(
        globalFromMesh,
        globalFromField,
        evalCoords,
        method = 'linear'
        )
    if checkNaN:
        nanFound = np.isnan(np.sum(data))
        if nanFound:
            raise exceptions.NaNFound(
                '''Nan value detected in array: ''' \
                '''to ignore, flag checkNaN = False'''
                )
    return data

def safe_box_evaluate(
        var,
        boxCoords,
        maxTolerance = None,
        fromMesh = None,
        globalFromMesh = None,
        globalFromField = None,
        ):
    if maxTolerance is None:
        maxTolerance = 1e-1
    tolerance = 1e-8
    if fromMesh is None:
        fromMesh = utilities.get_mesh(var)
    if globalFromMesh is None:
        globalFromMesh = get_global_var_data(fromMesh)
    if globalFromField is None:
        globalFromField = get_global_var_data(var)
    while tolerance < maxTolerance:
        try:
            data = box_evaluate(
                var,
                boxCoords,
                tolerance,
                fromMesh,
                globalFromMesh,
                globalFromField
                )
            return data
        except exceptions.NaNFound:
            tolerance *= 10.
    raise exceptions.AcceptableToleranceNotFound(
        '''Acceptable tolerance could not be found.'''
        )

def copyField(
        fromField,
        toField,
        maxTolerance = None
        ):
    toMesh = utilities.get_mesh(toField)
    boxCoords = mapping.box(
        toMesh,
        toMesh.data
        )
    copyData = safe_box_evaluate(
        fromField,
        boxCoords,
        maxTolerance
        )
    toField.data[...] = copyData
