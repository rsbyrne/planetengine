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

def weightVar(mesh, specialSets = None):

    maskVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)
    weightVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)

    if specialSets == None:
        localIntegral = uw.utils.Integral(maskVar, mesh)
    else:
        localIntegral = uw.utils.Integral(
            maskVar,
            mesh,
            integrationType = 'surface',
            surfaceIndexSet = specialSets
            )

    for index, val in enumerate(weightVar.data):
        maskVar.data[:] = 0.
        maskVar.data[index] = 1.
        weightVar.data[index] = localIntegral.evaluate()[0]
    return weightVar

def get_fullLocalMeshVar(field1):
    fullInField = None
    if field1.__hash__() in fullLocalMeshVars:
        fullInField = fullLocalMeshVars[field1.__hash__()]()
    if fullInField is None:
        fullInField = make_fullLocalMeshVar(field1)
    return fullInField

def make_fullLocalMeshVar(field1):

    if type(field1) == uw.mesh._meshvariable.MeshVariable:
        inMesh = field1.mesh
        inDim = field1.nodeDofCount
    elif type(field1) == uw.swarm._swarmvariable.SwarmVariable:
        inMesh = field1.swarm.mesh
        inDim = field1.count
    else:
        inMesh = utilities.get_mesh(field1)
        inDim = utilities.get_varDim(field1)
    meshUtils = get_meshUtils(inMesh)
    inField = meshUtils.meshify(
        field1,
        vector = inDim == inMesh.dim,
        update = False
        )
    localAnnulus = meshUtils.get_full_local_mesh()
    fullInField = localAnnulus.add_variable(inDim)

    def update():
        if hasattr(inField, 'project'):
            inField.project()
        allData = mpi.comm.gather(inField.data, root = 0)
        allGID = mpi.comm.gather(inField.mesh.data_nodegId, root = 0)
        if mpi.rank == 0:
            for proc in range(mpi.size):
                for data, ID in zip(allData[proc], allGID[proc]):
                    fullInField.data[ID] = data
        fullInField.data[:] = mpi.comm.bcast(fullInField.data, root = 0)

        try_set_scales(fullInField, field1)
        try_set_boundaries(fullInField, field1)

    # POSSIBLE CIRCULAR REFERENCE:
    fullInField.update = update

    fullLocalMeshVars[field1.__hash__()] = weakref.ref(fullInField)

    return fullInField

def copyField(field1, field2,
        tolerance = 0.01,
        rounded = False,
        boxDims = None,
        freqs = None,
        mirrored = None,
        blendweight = None
        # scales = None,
        # boundaries = None
        ):

    if not boxDims is None:
        assert np.max(np.array(boxDims)) <= 1., "Max boxdim is 1."
        assert np.min(np.array(boxDims)) >= 0., "Min boxdim is 0."

    utilities.check_uw(field1)

    if type(field2) == uw.mesh._meshvariable.MeshVariable:
        outMesh = field2.mesh
        outCoords = outMesh.data
        outDim = field2.nodeDofCount
    elif type(field2) == uw.swarm._swarmvariable.SwarmVariable:
        outMesh = field2.swarm.mesh
        outCoords = field2.swarm.particleCoordinates.data
        outDim = field2.count
    else:
        projVar = _projection.get_meshVar(field1)
        field2 = projVar.var
        outMesh = field2.mesh
        outCoords = outMesh.data
        outDim = field2.nodeDofCount
        # raise Exception("Input 2 not a field.")
    outField = field2

    fullInField = get_fullLocalMeshVar(field1)
    fullInField.update()
    inDim = fullInField.nodeDofCount
    inMesh = fullInField.mesh

    assert outDim == inDim, \
        "In and Out fields have different dimensions!"
    assert outMesh.dim == inMesh.dim, \
        "In and Out meshes have different dimensions!"

    outBox = mapping.box(
        outMesh,
        outCoords,
        boxDims,
        freqs,
        mirrored
        )

    def mapFn(tolerance):

        evalCoords = mapping.unbox(
            inMesh,
            outBox,
            tolerance = tolerance
            )

        newData = fullInField.evaluate(evalCoords)
        oldData = outField.data[:]
        if not blendweight is None:
            newData = np.sum(
                np.array([oldData, blendweight * newData]),
                axis = 0
                ) \
                / (blendweight + 1)

        outField.data[:] = newData

        # message("Mapping achieved at tolerance = " + str(tolerance))
        return tolerance

    tryTolerance = 0.

    while True:
        try:
            tryTolerance = mapFn(tryTolerance)
            break
        except:
            if tryTolerance > 0.:
                tryTolerance *= 1.01
            else:
                tryTolerance += 0.00001
            if tryTolerance > tolerance:
                raise Exception("Couldn't find acceptable tolerance.")
            else:
                pass

    if rounded:
        field2.data[:] = np.around(field2.data)

    # if not scales is None:
    #     set_scales(field2, scales)
    #
    # if not boundaries is None:
    #     set_boundaries(field2, boundaries)

    try_set_scales(field2, field1)
    try_set_boundaries(field2, field1)
    try_set_scales(field2)
    try_set_boundaries(field2)

    return tryTolerance
