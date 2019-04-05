import numpy as np

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

def rescale_coords(
        coordArray,
        inScales,
        outScales,
        flip = None
        ):

    transposed = coordArray.transpose()
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

def box(mesh, coordArray = None):
    if coordArray is None:
        coordArray = mesh.data
    outArray = rescale_coords(
        radial_coords(coordArray),
        (mesh.angularExtent, mesh.radialLengths),
        ((0., 1), (0., 1.)),
        flip = [True, False]
        )
    return outArray

def unbox(mesh, coordArray = None):
    if coordArray is None:
        coordArray = mesh.data
    outArray = radial_coords(
        rescale_coords(
            coordArray,
            ((0., 1), (0., 1.)),
            (mesh.angularExtent, mesh.radialLengths),
            flip = [True, False]
            ),
        inverse = True
        )
    return outArray