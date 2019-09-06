import sys
import os
import shutil
workpath = '/home/jovyan/workspace'
sys.path.append('/home/jovyan/workspace')
outputPath = os.path.join(workpath, 'data/test')
if os.path.isdir(outputPath):
    shutil.rmtree(outputPath)
os.mkdir(outputPath)
os.chmod(outputPath, 777)

import planetengine
import underworld as uw
from underworld import function as fn
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
