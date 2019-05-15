import numpy as np

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

def get_scales(variable, partitioned = False):
    scales = []
    if type(variable) == np.ndarray:
        data = variable
    else:
        data = variable.data
    if partitioned:
        data = comm.gather(data, root = 0)
    if rank == 0:
        for i in range(data.shape[1]):
            scales.append(
                data[:,i].min(),
                data[:,i].max()
                )
    scales = comm.bcast(scales, root = 0)
    return scales

def recentered_coords(
        coordArray,
        origin = (0., 0.),
        inverse = False,
        ):

    if not inverse:
        outArray = coordArray - origin
    else:
        outArray = coordArray + origin

    return outArray

def radial_coords(
        coordArray,
        origin = (0., 0.),
        inverse = False,
        ):

    recenteredCoords = recentered_coords(coordArray, origin, inverse)

    if not inverse:
        xs, ys = recenteredCoords.transpose()
        angular = np.arctan2(ys, xs) * 180. / np.pi
        #angular = np.where(xs >= 0., angular, angular + 360.)
        radial = np.hypot(xs, ys)
        outArray = np.dstack((angular, radial))[0]

    else:
        angular, radial = recenteredCoords.transpose()
        xs = radial * np.cos(angular * np.pi / 180.)
        ys = radial * np.sin(angular * np.pi / 180.)
        outArray = np.dstack((xs, ys))[0]

    return outArray

def rescale_array(
        inArray,
        inScales,
        outScales,
        flip = None
        ):

    transposed = inArray.transpose()
    outVals = []
    for nD in range(len(transposed)):
        vals = transposed[nD]
        inScale = inScales[nD]
        outScale = outScales[nD]
        inRange = inScale[1] - inScale[0]
        outRange = outScale[1] - outScale[0]
        inMin, inMax = inScale
        outMin, outMax = outScale
        vals = ((vals - inMin) / inRange)
        if not flip == None:
            if flip[nD]:
                vals = 1. - vals
        vals = vals * outRange + outMin
        vals = np.clip(vals, outMin, outMax)
        outVals.append(vals)
    outArray = np.dstack(outVals)[0]
    return outArray

def box(mesh, coordArray = None, boxDims = ((0., 1), (0., 1.))):
    if coordArray is None:
        coordArray = mesh.data
    outArray = rescale_array(
        radial_coords(coordArray),
        (mesh.angularExtent, mesh.radialLengths),
        boxDims,
        flip = [True, False]
        )
    return outArray

def unbox(mesh, coordArray = None, boxDims = ((0., 1), (0., 1.))):
    if coordArray is None:
        coordArray = mesh.data
    outArray = radial_coords(
        rescale_array(
            coordArray,
            boxDims,
            (mesh.angularExtent, mesh.radialLengths),
            flip = [True, False]
            ),
        inverse = True
        )
    return outArray