from .. import initials
from .. import model
from .. import systems
from ..utilities import message
import underworld as uw
from underworld import function as fn

from ..paths import TestDir

def testfn():
    with TestDir() as outputPath:
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
        model2 = model.make_model(
            system = systems.arrhenius.build(res = 32, f = 1.),
            initials = {'temperatureField': initials.load.build(inFrame = model0, varName = 'temperatureField')},
            outputPath = outputPath
            )
        model2.iterate()
        model2.unarchive()
        model2.archive()
        model2.checkpoint()
        model3 = model.load_model(model1.outputPath, model1.instanceID)
        message('Success!')
