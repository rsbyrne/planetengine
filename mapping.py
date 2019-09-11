import numpy as np
import math
import underworld as uw

from . import meshutils
get_meshUtils = meshutils.get_meshUtils

def get_pureBoxDims(coordArray):
    pureBoxDims = ((0., 1.),) * coordArray.shape[1]
    return pureBoxDims

def get_pureFreqs(coordArray):
    pureFreqs = tuple([1. for dim in range(coordArray.shape[1])])
    return pureFreqs

def boundary_interpolate(fromData, toData, dim):
    # NOT PARALLEL SAFE

    assert uw.mpi.size == 1

    fromField, fromMesh, fromIndexSet = fromData
    comp = 0
    outArrs = []
    while comp < dim:
        coordSet = fromMesh.data[fromIndexSet]
        previousCoord = coordSet[0]
        cumulativeDistance = 0.
        fromPositions = []
        fromValues = []
        for index, currentCoord in enumerate(coordSet):
            cumulativeDistance += math.hypot(
                currentCoord[0] - previousCoord[0],
                currentCoord[1] - previousCoord[1]
                )
            value = fromField.data[list(fromIndexSet)[index]][comp]
            fromPositions.append(cumulativeDistance)
            fromValues.append(value)
            previousCoord = currentCoord

        toField, toMesh, toIndexSet = toData
        coordSet = toMesh.data[toIndexSet]
        previousCoord = coordSet[0]
        cumulativeDistance = 0.
        toPositions = []
        for index, currentCoord in enumerate(coordSet):
            cumulativeDistance += math.hypot(
                currentCoord[0] - previousCoord[0],
                currentCoord[1] - previousCoord[1]
                )
            toPositions.append(cumulativeDistance)
            previousCoord = currentCoord

        toValues = np.interp(toPositions, fromPositions, fromValues)
        outArrs.append(toValues)
        comp += 1

    outArr = np.dstack(outArrs)

    toField.data[toIndexSet] = outArr

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
        angular = np.where(angular >= 0., angular, angular + 360.)
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
        flip = None,
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

def modulate(
        coordArray,
        boxDims = None,
        freqs = None,
        mirrored = None,
        ):

    pureBoxDims = get_pureBoxDims(coordArray)

    if boxDims is None:
        boxDims = pureBoxDims

    if freqs is None:
        freqs = [1. for x in boxDims]
    assert len(freqs) == len(boxDims)

    outArray = coordArray.copy()

    freqDims = (np.array(pureBoxDims).T * freqs).T
    outArray = rescale_array(outArray, boxDims, freqDims)
    outArray %= (1. + 1e-15)
    outArray = rescale_array(outArray, pureBoxDims, boxDims)

    if not mirrored is None:
        assert len(mirrored) == len(boxDims)
        multArr = [1. + int(boolean) for boolean in mirrored]
        addArr = [1. * int(boolean) for boolean in mirrored]
        outArray = rescale_array(outArray, boxDims, pureBoxDims)
        outArray = abs(outArray * multArr - addArr)
        outArray = rescale_array(outArray, pureBoxDims, boxDims)

    return outArray

def shrink_box(
        coordArray,
        boxDims = None,
        tolerance = 0.01,
        ):

    pureBoxDims = get_pureBoxDims(coordArray)
    if boxDims is None:
        boxDims = pureBoxDims

    # scale to unit box if necessary:
    if not boxDims == pureBoxDims:
        outBox = rescale_array(
            coordArray,
            boxDims,
            pureBoxDims
            )
    else:
        outBox = coordArray

    # shrink the box to a specified tolerance:
    adjBoxDims = ((0. + tolerance, 1. - tolerance),) * outBox.shape[1]
    outBox = rescale_array(
        outBox,
        pureBoxDims,
        adjBoxDims
        )

    # return box to original dimensions:
    if not boxDims == pureBoxDims:
        outBox = rescale_array(
            outBox,
            pureBoxDims,
            boxDims
            )

    return outBox

def box(
        mesh,
        coordArray = None,
        boxDims = None,
        freqs = None,
        mirrored = None,
        ):

    if coordArray is None:
        coordArray = mesh.data

    if boxDims is None:
        boxDims = get_pureBoxDims(coordArray)

    if type(mesh) == uw.mesh.FeMesh_Annulus:
        radialCoords = radial_coords(coordArray)
        inScales = [mesh.angularExtent, mesh.radialLengths]
        outScales = boxDims
        outArray = rescale_array(
            radialCoords,
            inScales,
            outScales,
            flip = [True, True]
            )
    else:
        outArray = rescale_array(
            coordArray,
            list(zip(mesh.minCoord, mesh.maxCoord)),
            boxDims,
            flip = [False, True]
            )

    if (not freqs is None) or (not mirrored is None):
        outArray = modulate(
            outArray,
            boxDims,
            freqs,
            mirrored
            )

    return outArray

def unbox(
        mesh,
        coordArray = None,
        boxDims = None,
        tolerance = 0.,
        ):

    meshUtils = get_meshUtils(mesh)

    if coordArray is None:
        coordArray = mesh.data[:]
    pureBoxDims = get_pureBoxDims(coordArray)
    if boxDims is None:
        boxDims = pureBoxDims

    inBox = coordArray

    if tolerance > 0.:
        inBox = shrink_box(coordArray, boxDims, tolerance)
    else:
        inBox = coordArray

    outBoxDims = (mesh.angularExtent, mesh.radialLengths)

    outArray = radial_coords(
        rescale_array(
            inBox,
            boxDims,
            outBoxDims,
            flip = meshUtils.flip
            ),
        inverse = True
        )

    return outArray
