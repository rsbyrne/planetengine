from .. import initials
from .. import frame
from .. import systems
from ..utilities import message
import underworld as uw
from underworld import function as fn

from ..paths import TestDir

def testfn():
    with TestDir() as outputPath:
        inModel = frame.make_frame(
            systems.arrhenius.build(res = 32, f = 0.5),
            {'temperatureField': initials.sinusoidal.IC()},
            outputPath = outputPath
            )
        model = frame.make_frame(
            systems.arrhenius.build(res = 32, f = 1.),
            {'temperatureField': initials.load.IC(inModel, 'temperatureField')},
            outputPath = outputPath
            )
        model.checkpoint()
        model2 = frame.make_frame(
            systems.arrhenius.build(res = 32, f = 1.),
            {'temperatureField': initials.load.IC(inModel, 'temperatureField')},
            outputPath = outputPath
            )
        model2.iterate()
        model2.unarchive()
        model2.archive()
        model2.checkpoint()
        message('Success!')
