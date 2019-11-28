import numpy as np
import math
import underworld as uw
fn = uw.function

from . import mpi
from . import utilities
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

    assert mpi.size == 1

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

    assert not any([
        scale in ['.', '!'] \
            for scale in inScales
        ])
    assert not any([
        scale in ['.', '!'] \
            for scale in outScales
        ])

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
    if not np.allclose(boxDims, pureBoxDims):
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
    if not np.allclose(boxDims, pureBoxDims):
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

    meshUtils = get_meshUtils(mesh)

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
            flip = meshUtils.flip
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
        shrinkLocal = False
        ):

    meshUtils = get_meshUtils(mesh)

    if coordArray is None:
        coordArray = mesh.data[:]
    if boxDims is None:
        boxDims = get_pureBoxDims(coordArray)

    inBox = coordArray

    if tolerance > 0.:
        if shrinkLocal:
            shrinkBox = utilities.get_scales(inBox, local = True)
        else:
            shrinkBox = boxDims
        inBox = shrink_box(coordArray, shrinkBox, tolerance)
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

def safe_box_evaluate(inFn, inCoords, maxTolerance = 0.1):
    tolerance = 0.
    while tolerance < maxTolerance:
        try:
            outArray = box_evaluate(inFn, inCoords, tolerance)
            break
        except:
            if tolerance == 0.:
                tolerance += 0.00001
            else:
                tolerance *= 1.01
    if tolerance > maxTolerance:
        raise Exception("Acceptable tolerance could not be found.")
    return outArray, tolerance

def box_evaluate(inFn, inCoords, tolerance):
    mesh = utilities.get_mesh(inFn)
    unboxed = unbox(
        mesh,
        inCoords,
        tolerance = tolerance
        )
    localValsDict = {}
    for coords in unboxed:
        try: localValsDict[tuple(coords)] = inFn.evaluate(np.array([coords,]))[0]
        except: pass
    allValsDicts = mpi.comm.allgather(localValsDict)
    globalValsDict = {}
    for localValDict in allValsDicts:
        globalValsDict.update(localValDict)
    outVals = []
    for coord in unboxed:
        outVals.append(globalValsDict[tuple(coord)])
    outArray = np.array(outVals)
    if not outArray.shape[0] == inCoords.shape[0]:
        raise Exception("Some coords could not be evaluated!")
    return outArray

def get_localInCoords(inCoords, mesh, boxInput = True):
    if not boxInput:
        inCoords = box(mesh, inCoords)
    localBox = box(mesh)
    localBoxScales = utilities.get_scales(
        localBox,
        local = True
        )
    localBoxVertices = np.vstack(
        np.dstack(
            np.meshgrid(
                localBoxScales[0],
                localBoxScales[1]
                )
            )
        )
    rearrangedLocalBoxVertices = np.array([
        localBoxVertices[0],
        localBoxVertices[1],
        localBoxVertices[3],
        localBoxVertices[2]
        ])
    localBoxPoly = fn.shape.Polygon(
        rearrangedLocalBoxVertices
        )
    localIndices, nonlocalIndices = np.where(
        localBoxPoly.evaluate(
            inCoords
            )
        )
    localInCoords = inCoords[localIndices]
    if not boxInput:
        localInCoords = unbox(
            mesh,
            localInCoords
            )
    return localInCoords

def safe_local_box_evaluate(inFn, inCoords, maxTolerance = 0.001):
    mesh = utilities.get_mesh(inFn)
    localInCoords = get_localInCoords(inCoords, mesh)
    tolerance = 0.
    while tolerance < maxTolerance:
        try:
            unboxedLocalInCoords = unbox(
                mesh,
                localInCoords,
                tolerance = tolerance
                )
            outArray = inFn.evaluate(unboxedLocalInCoords)
            break
        except:
            if tolerance == 0.:
                tolerance += 0.00001
            else:
                tolerance *= 1.01
    if tolerance > maxTolerance:
        raise Exception("Acceptable tolerance could not be found.")
    return outArray, tolerance

def local_box_evaluate(inFn, inCoords, tolerance = 0.1):
    mesh = utilities.get_mesh(inFn)
    localInCoords = get_localInCoords(inCoords, mesh)
    unboxedLocalInCoords = unbox(
        mesh,
        localInCoords,
        tolerance = tolerance,
        shrinkLocal = True
        )
    outArray = inFn.evaluate(unboxedLocalInCoords)
    return outArray, tolerance
