import planetengine
import underworld as uw
from underworld import function as fn
from planetengine import Grouper
from planetengine import InitialConditions as InitialConditions

def build():

    ### HOUSEKEEPING: IMPORTANT! ###

    inputs = locals().copy()
    script = __file__

    ### INITIALS ###

    def apply(system):

        system.step.value = 0
        system.modeltime.value = 0.

        curvedBox = planetengine.CoordSystems.Radial(
            system.mesh.radialLengths,
            system.mesh.angularExtent,
            boxDims = ((0., 1.), (0., 1.))
            ).curved_box(
                system.mesh.data
                )

        initialConditions = InitialConditions.Group([
            InitialConditions.Sinusoidal(system.temperatureField.data, curvedBox),
            InitialConditions.Indices(
                system.temperatureField.data,
                [(system.outer.data, 0.),
                (system.inner.data, 1.)]
                ),
            InitialConditions.SetVal(
                [system.velocityField.data, system.pressureField.data, system.temperatureDotField.data],
                0.
                ),
            ])

        initialConditions.apply()
        system.solve()

    ### HOUSEKEEPING: IMPORTANT! ###
    return Grouper(locals())