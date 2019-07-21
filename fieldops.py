from .meshutils import get_meshUtils
from . import mapping

import underworld as uw
from underworld import function as fn

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    meshUtils = get_meshUtils(variable.mesh)
    walls = meshUtils.wallsList

    for i, component in enumerate(values):
        for value, wall in zip(component, walls):
            if not value is '.':
                variable.data[wall, i] = value

def set_scales(variable, values):

    variable.data[:] = mapping.rescale_array(
        variable.data,
        get_scales(variable),
        values
        )

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
    for proc in range(nProcs):
        if rank == proc:
            localAnn = uw.mesh.FeMesh_Annulus(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                radialLengths = mesh.radialLengths,
                angularExtent = mesh.angularExtent,
                periodic = mesh.periodic,
                partitioned = False,
                )
    return localAnn

def makeLocalCart(mesh):
    for proc in range(nProcs):
        if rank == proc:
            localMesh = uw.mesh.FeMesh_Cartesian(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                minCoord = mesh.minCoord,
                maxCoord = mesh.maxCoord,
                periodic = mesh.periodic,
                partitioned = False,
                )
    return localMesh

def copyField(field1, field2,
        tolerance = 0.01,
        rounded = False,
        boxDims = None,
        freqs = None,
        mirrored = None,
        blendweight = None,
        scales = None,
        boundaries = None,
        ):

    if not boxDims is None:
        assert np.max(np.array(boxDims)) <= 1., "Max boxdim is 1."
        assert np.min(np.array(boxDims)) >= 0., "Min boxdim is 0."

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

    fullInField = makeLocalAnnulus(inMesh).add_variable(inDim)
    allData = comm.gather(inField.data, root = 0)
    allGID = comm.gather(inField.mesh.data_nodegId, root = 0)
    if rank == 0:
        for proc in range(nProcs):
            for data, ID in zip(allData[proc], allGID[proc]):
                fullInField.data[ID] = data
    fullInField.data[:] = comm.bcast(fullInField.data, root = 0)

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

        message("Mapping achieved at tolerance = " + str(tolerance))
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

    if not scales is None:
        set_scales(field2, scales)

    if not boundaries is None:
        set_boundaries(field2, boundaries)

    del field1Proj
    del field1Projector
    del fullInField
    del allData
    del allGID

    return tryTolerance
