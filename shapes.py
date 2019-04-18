def trapezoid(
        centre = 0.5,
        longwidth = 0.3,
        shortwidth = 0.2,
        thickness = 0.1,
        skew = 0.,
        location = 'surface',
        ratio = None,
        taper = None,
        thicknessRatio = None,
        ):

    if thicknessRatio is None:
        thicknessRatio = thickness / longwidth
    else:
        thickness = thicknessRatio * longwidth

    if ratio is None:
        if taper is None:
            taper = (longwidth - shortwidth) / 2 / thickness
        else:
            shortwidth = longwidth - 2. * taper * thickness
        ratio = shortwidth / longwidth
    else:
        shortwidth = ratio * longwidth
        if taper is None:
            taper = (longwidth - shortwidth) / 2 / thickness
        else:
            raise Exception("Cannot specify both taper and ratio.")

    if location == 'surface':
        shape = (
            (centre - longwidth * ratio / 2. + skew * longwidth, 1. - thickness),
            (centre - longwidth / 2., 1.),
            (centre + longwidth / 2., 1.),
            (centre + longwidth * ratio / 2. + skew * longwidth, 1. - thickness),
            )
    elif location == 'base':
        shape = (
            (centre - longwidth / 2., 0.),
            (centre - longwidth * ratio / 2. + skew * longwidth, thickness),
            (centre + longwidth * ratio / 2. + skew * longwidth, thickness),
            (centre + longwidth / 2., 0.),
            )

    else:
        raise Exception("Only 'surface' and 'base' locations are accepted")

    return shape