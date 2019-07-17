import numpy as np

def trapezoid(
        centre = 0.5,
        longwidth = 0.3,
        shortwidth = 0.2,
        thickness = 0.1,
        skew = 0.,
        location = 'surface',
        lengthRatio = None,
        taper = None,
        thicknessRatio = None,
        ):

    if thicknessRatio is None:
        thicknessRatio = thickness / longwidth
    else:
        thickness = thicknessRatio * longwidth

    if lengthRatio is None:
        if taper is None:
            taper = (longwidth - shortwidth) / 2 / thickness
        else:
            shortwidth = longwidth - 2. * taper * thickness
        lengthRatio = shortwidth / longwidth
    else:
        shortwidth = lengthRatio * longwidth
        if taper is None:
            taper = (longwidth - shortwidth) / 2 / thickness
        else:
            raise Exception("Cannot specify both taper and ratio.")

    # shape is drawn by clockwise order of vertices:
    if location == 'surface':
        shape = (
            (centre - longwidth * lengthRatio / 2. + skew * longwidth, 1. - thickness),
            (centre - longwidth / 2., 1.),
            (centre + longwidth / 2., 1.),
            (centre + longwidth * lengthRatio / 2. + skew * longwidth, 1. - thickness),
            )
    elif location == 'base':
        shape = (
            (centre - longwidth / 2., 0.),
            (centre - longwidth * lengthRatio / 2. + skew * longwidth, thickness),
            (centre + longwidth * lengthRatio / 2. + skew * longwidth, thickness),
            (centre + longwidth / 2., 0.),
            )
        shape = np.array(shape)

    else:
        raise Exception("Only 'surface' and 'base' locations are accepted")

    return shape