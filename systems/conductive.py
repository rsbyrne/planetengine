import underworld as uw
fn, cd = uw.function, uw.conditions

from planetengine.systems import System
from planetengine.meshes import Annulus

class Conductive(System):

    optionsKeys = {
        'res', 'meshClass'
        }
    paramsKeys = {
        'aspect', 'f', 'flux', 'H', 'kappa', 'length', 'tempDelta', 'tempRef'
        }
    configsKeys = {
        'temperatureField',
        }

    def __init__(self,
            # OPTIONS
            res = 64,
            meshClass = Annulus,
            # PARAMS
            aspect = 1.,
            f = 1.,
            flux = None,
            H = 0.,
            kappa = 1.,
            length = 1.,
            tempDelta = 1.,
            tempRef = 0.,
            # CONFIGS
            temperatureField = None,
            # META
            **kwargs
            ):

        tempMin, tempMax = tempRef, tempRef + tempDelta

        ### MESH ###

        mesh = meshClass(
            res = res,
            aspect = aspect,
            f = f,
            length = length
            )

        ### VARIABLES ###

        temperatureField = mesh.add_variable(1)

        ### BOUNDARIES ###

        specSets = mesh.specialSets
        inner, outer = specSets['inner'], specSets['outer']

        if flux is None and H == 0.:
            temperatureField.scales = [[tempMin, tempMax]]
            temperatureField.bounds = [[tempMin, tempMax, '.', '.']]
        else:
            temperatureField.scales = [[tempMin, None]]
            temperatureField.bounds = [[tempMax, '.', '.', '.']]

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
