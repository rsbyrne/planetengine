from .. import initials
from .. import model
from .. import systems
from ..utilities import message
from .. import paths

def testfn():

    with paths.TestDir() as outputPath:

        model0 = model.make_model(
            system = systems.arrhenius.build(res = 32, f = 0.5),
            initials = {'temperatureField': initials.sinusoidal.build()},
            outputPath = outputPath
            )
        model1 = model.make_model(
            system = systems.arrhenius.build(res = 32, f = 1.),
            initials = {'temperatureField': initials.load.build(inFrame = model0, varName = 'temperatureField')},
            outputPath = outputPath
            )
        model1.checkpoint()
        model1.unarchive()
        model1.archive()
        model2 = model.make_model(
            system = systems.arrhenius.build(res = 32, f = 1.),
            initials = {'temperatureField': initials.load.build(inFrame = model0, varName = 'temperatureField')},
            outputPath = outputPath
            )
        model2.iterate()
        model2.unarchive()
        model2.archive()
        model2.checkpoint()
        model2.unarchive()
        message('Success!')
