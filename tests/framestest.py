import planetengine
import underworld as uw
from underworld import function as fn

from .testdir import TestDir

def testfn():
    with TestDir() as outputPath:
        inModel = planetengine.frame.make_frame(
            planetengine.systems.arrhenius.build(res = 16, f = 0.5),
            {'temperatureField': planetengine.initials.sinusoidal.IC()},
            outputPath = '../data/test'
            )
        model = planetengine.frame.make_frame(
            planetengine.systems.arrhenius.build(res = 16, f = 1.),
            {'temperatureField': planetengine.initials.load.IC(inModel, 'temperatureField')},
            outputPath = '../data/test'
            )
        model.checkpoint()
        model2 = planetengine.frame.make_frame(
            planetengine.systems.arrhenius.build(res = 16, f = 1.),
            {'temperatureField': planetengine.initials.load.IC(inModel, 'temperatureField')},
            outputPath = '../data/test'
            )
        model2.iterate()
        model2.unarchive()
        model2.archive()
        model2.checkpoint()
        planetengine.message('Success!')
