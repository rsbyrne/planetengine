import planetengine

from planetengine import model
from planetengine import systems
from planetengine import initials
from planetengine import paths

with paths.TestDir() as outputPath:

    IC0 = {
        'temperatureField': initials.sinusoidal.build(
            initials.sinusoidal.build(
                freq = 2,
                pert = 0.4
                )
            )
        }

    system0 = systems.arrhenius.build(res = 32, f = 0.5)

    model0 = model.make_model(
        system = system0,
        initials = IC0,
        outputPath = outputPath
        )

    model0.iterate()

    model0.checkpoint()

    IC1 = {
        'temperatureField': initials.load.build(
            inFrame = model0,
            varName = 'temperatureField'
            )
        }

    system1 = systems.arrhenius.build(res = 32, f = 1.)

    model1 = model.make_model(
        system = system1,
        initials = IC1,
        outputPath = outputPath
        )

    model1.checkpoint()

    model1.iterate()

    model1.checkpoint()

    model1_load = model.load_model(outputPath, model1.instanceID)

    model1_load.iterate()

    model1_load.checkpoint()

    model1_load.unarchive()

    model1_load.archive()

    IC2 = {
        'temperatureField': initials.load.build(
            IC0['temperatureField'],
            initials.sinusoidal.build(freq = 10., pert = 0.6),
            inFrame = model0,
            varName = 'temperatureField'
            )
        }

    system2 = systems.arrhenius.build(res = 32, f = 0.7)

    model2 = model.make_model(
        system = system2,
        initials = IC2,
        outputPath = outputPath
        )

    model2.checkpoint()

    model2.iterate()

    model2.checkpoint()
