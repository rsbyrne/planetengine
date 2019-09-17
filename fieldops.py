import numpy as np

import underworld as uw
from underworld import function as fn

from .meshutils import get_meshUtils
from . import mapping
from .utilities import get_scales
from .utilities import message

from . import mpi

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    meshUtils = get_meshUtils(variable.mesh)
    walls = meshUtils.wallsList

    if values is None:
        try:
            values = variable.bounds
        except:
            raise Exception

    for i, component in enumerate(values):
        for value, wall in zip(component, walls):
            if not value is '.':
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

def makeLocalAnnulus(mesh):
    for proc in range(mpi.size):
        if mpi.rank == proc:
            localAnn = uw.mesh.FeMesh_Annulus(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                radialLengths = mesh.radialLengths,
                angularExtent = mesh.angularExtent,
                periodic = mesh.periodic,
                partitioned = False,
                )
    # mpi.barrier()
    return localAnn

def makeLocalCart(mesh):
    for proc in range(mpi.size):
        if mpi.rank == proc:
            localMesh = uw.mesh.FeMesh_Cartesian(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                minCoord = mesh.minCoord,
                maxCoord = mesh.maxCoord,
                periodic = mesh.periodic,
                partitioned = False,
                )
    # mpi.barrier()
    return localMesh

def make_fullLocalMeshVar(field1):

    if type(field1) == uw.mesh._meshvariable.MeshVariable:
        inField = field1
        inMesh = field1.mesh
        inDim = field1.nodeDofCount
    else:
        inMesh = field1.swarm.mesh
        field1Proj = uw.mesh.MeshVariable(
            inMesh,
            field1.count,
            )
        field1Projector = uw.utils.MeshVariable_Projection(
            field1Proj,
            field1
            )
        field1Projector.solve()
        inField = field1Proj
        inDim = field1.count

    localAnnulus = makeLocalAnnulus(inMesh)
    fullInField = localAnnulus.add_variable(inDim)

    def update():
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
    fullInField.update()

    return fullInField

def copyField(field1, field2,
        tolerance = 0.01,
        rounded = False,
        boxDims = None,
        freqs = None,
        mirrored = None,
        blendweight = None,
        _fullLocalMeshVar = None
        # scales = None,
        # boundaries = None
        ):

    if not boxDims is None:
        assert np.max(np.array(boxDims)) <= 1., "Max boxdim is 1."
        assert np.min(np.array(boxDims)) >= 0., "Min boxdim is 0."

    if _fullLocalMeshVar is None:
        fullInField = make_fullLocalMeshVar(field1)
    else:
        fullInField = _fullLocalMeshVar
        fullInField.update()
    inDim = fullInField.nodeDofCount
    inMesh = fullInField.mesh

    outField = field2
    if type(field2) == uw.mesh._meshvariable.MeshVariable:
        outMesh = field2.mesh
        outCoords = outMesh.data
        outDim = field2.nodeDofCount
    else:
        outMesh = field2.swarm.mesh
        outCoords = field2.swarm.particleCoordinates.data
        outDim = field2.count

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
