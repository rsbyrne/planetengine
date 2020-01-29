import planetengine

planetengine.paths.delete_testdir()
outputPath = planetengine.paths.make_testdir()

system = planetengine.systems.arrhenius.get(
    planetengine.systems.isovisc.get(),
    Ra = 3e5,
    res = 16,
    f = 0.5
    )
initials = {
    'temperatureField': planetengine.initials.sinusoidal.get(
        planetengine.initials.sinusoidal.get(
            freq = 2,
            pert = 0.4
            )
        )
    }

model = planetengine.model.make_model(
    system = system,
    initials = initials,
    outputPath = outputPath
    )

model.iterate()

model.checkpoint()

model.unarchive()

model2 = planetengine.frame.load_frame(model.instanceID, outputPath)

model2.checkpoint()

model2.iterate()

model2.checkpoint()

model2.report()
