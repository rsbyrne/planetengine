import math

import underworld as uw
fn, cd = uw.function, uw.conditions

from planetengine.systems import System

class Conductive(System):

    optionsKeys = {
        'res'
        }
    paramsKeys = {
        'aspect', 'f', 'flux', 'H', 'kappa'
        }
    configsKeys = {
        'temperatureField',
        }

    def __init__(self,
            # OPTIONS
            res = 64,
            # PARAMS
            aspect = 1.,
            f = 1.,
            flux = None,
            H = 0.,
            kappa = 1.,
            # CONFIGS
            temperatureField = None,
            # META
            **kwargs
            ):

        ### MESH ###

        if f == 1. and aspect == 'max':
            raise ValueError
        maxf = 0.999
        if f == 'max' or f == 1.:
            f = maxf
        else:
            assert f <= maxf

        length = 1.
        outerRad = 1. / (1. - f)
        radii = (outerRad - length, outerRad)

        maxAspect = math.pi * sum(radii) / length
        if aspect == 'max':
            aspect = maxAspect
            periodic = True
        else:
            assert aspect < maxAspect
            periodic = False

        width = length**2 * aspect * 2. / (radii[1]**2 - radii[0]**2)
        midpoint = math.pi / 2.
        angExtentRaw = (midpoint - 0.5 * width, midpoint + 0.5 * width)
        angExtentDeg = [item * 180. / math.pi for item in angExtentRaw]
        angularExtent = [
            max(0., angExtentDeg[0]),
            min(360., angExtentDeg[1] + abs(min(0., angExtentDeg[0])))
            ]
        angLen = angExtentRaw[1] - angExtentRaw[0]

        assert res % 4 == 0
        radRes = res
        angRes = 4 * int(angLen * (int(radRes * radii[1] / length)) / 4)
        elementRes = (radRes, angRes)

        mesh = uw.mesh.FeMesh_Annulus(
            elementRes = elementRes,
            radialLengths = radii,
            angularExtent = angularExtent,
            periodic = [False, periodic]
            )

        ### VARIABLES ###

        temperatureField = mesh.add_variable(1)

        ### BOUNDARIES ###

        specSets = mesh.specialSets
        inner, outer = specSets['inner'], specSets['outer']

        if flux is None and H == 0.:
            temperatureField.scales = [[0., 1.]]
            temperatureField.bounds = [[0., 1., '.', '.']]
        else:
            temperatureField.scales = [[0., None]]
            temperatureField.bounds = [[0., '.', '.', '.']]

        if flux is None:
            tempBC = cd.DirichletCondition(temperatureField, (inner + outer,))
            tempBCs = [tempBC,]
        else:
            tempBC = cd.DirichletCondition(temperatureField, (outer,))
            tempFluxBC = cd.NeumannCondition(temperatureField, (inner,), flux)
            tempBCs = [tempBC, tempFluxBC]

        ### FUNCTIONS ###

        heatingFn = fn.misc.constant(H)
        diffusivityFn = fn.misc.constant(kappa)

        ### SYSTEMS ###

        steady = uw.systems.SteadyStateHeat(
            temperatureField = temperatureField,
            fn_diffusivity = diffusivityFn,
            fn_heating = heatingFn,
            conditions = tempBCs
            )

        solver = uw.systems.Solver(steady)

        ### SOLVING ###

        def update():
            solver.solve()

        def integrate():
            return 0.

        super().__init__(locals(), **kwargs)

### ATTRIBUTES ###
CLASS = Conductive
