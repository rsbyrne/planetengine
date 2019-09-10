from .. import initials
from .. import frames
from .. import systems
from ..utilities import message
import underworld as uw
from underworld import function as fn

from ..paths import TestDir

def testfn():
    with TestDir() as outputPath:
        model0 = frames.frame.make_frame(
            'model',
            systems.arrhenius.build(res = 32, f = 0.5),
            {'temperatureField': initials.sinusoidal.build()},
            outputPath = outputPath
            )
        model1 = frames.frame.make_frame(
            'model',
            systems.arrhenius.build(res = 32, f = 1.),
            {'temperatureField': initials.sinusoidal.build()},
            # {'temperatureField': initials.load.build(model0, 'temperatureField')},
            outputPath = outputPath
            )
        model1.checkpoint()
        model2 = frames.frame.make_frame(
            'model',
            systems.arrhenius.build(res = 32, f = 1.),
            {'temperatureField': initials.sinusoidal.build()},
            # {'temperatureField': initials.load.build(model0, 'temperatureField')},
            outputPath = outputPath
            )
        model2.iterate()
        model2.unarchive()
        model2.archive()
        model2.checkpoint()
        model3 = frames.frame.load_frame(outputPath, model1.instanceID)
        message('Success!')
