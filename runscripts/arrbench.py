import sys
workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)

import os

import planetengine

outDir = planetengine.paths.defaultPath

projName = 'arrbench'
projBranch = ''
outputPath = os.path.join(outDir, projName, projBranch)

chunks = int(sys.argv[1])
chunkno = int(sys.argv[2])
iterno = int(sys.argv[3])

suitelist = planetengine.utilities.suite_list({
    'f': [0.2, 0.4, 0.6, 0.8, 1.],
    'eta0': [1., 10., 100., 1000., 10000.],
    'Ra': [1e3, 1e4, 1e5, 1e6, 1e7],
    }, shuffle = True, chunks = chunks)

job = suitelist[chunkno][iterno]

planetengine.log(
    "Starting chunk no# " + str(chunkno) + ", iter no# " + str(iterno),
    'logs'
    )

model = planetengine.model.make_model(
    planetengine.systems.arrhenius.build(res = 16, **job),
    {'temperatureField': planetengine.initials.sinusoidal.build(freq = 1.)},
    outputPath = outputPath
    )

if len(model.checkpoints) > 0:
    model.load_checkpoint('max')

observer = planetengine.observers.standard.build()
observer.attach(model)

conditions = {
    # 'stopCondition': lambda: model.modeltime() > 0.3,
    'stopCondition': lambda: model.step() > 25,
    'checkpointCondition': lambda: any([
        model.status == 'pre-traverse',
        model.step() % 1000 == 0,
        model.status == 'post-traverse',
        ]),
    }

model.traverse(**conditions)

planetengine.log(
    "Finishing chunk no# " + str(chunkno) + ", iter no# " + str(iterno),
    'logs'
    )
