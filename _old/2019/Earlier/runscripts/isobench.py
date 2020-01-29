import sys
workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)

import os

import planetengine

outDir = planetengine.paths.defaultPath

projName = 'isobench'

chunks = int(sys.argv[1])
shuffleseed = int(sys.argv[2])
chunkno = int(sys.argv[3])
iterno = int(sys.argv[4])

suitelist = planetengine.suite.suite_list({
    'f': [round(x / 10., 1) for x in range(1, 11)],
    'Ra': [round(10.**(x / 2.), 0) for x in range(6, 16)],
    'aspect': [1. * (x / 4.) for x in range(4, 14)],
    'res': [16, 32, 64]
    }, shuffle = True, chunks = chunks, shuffleseed = shuffleseed)

job = suitelist[chunkno][iterno]

projBranch = 'res' + str(job['res'])
outputPath = os.path.join(outDir, projName, projBranch)

planetengine.log(
    "Starting chunk no# " + str(chunkno) + ", iter no# " + str(iterno),
    'logs'
    )

model = planetengine.model.make_model(
    planetengine.systems.isovisc.get(**job),
    {'temperatureField': planetengine.initials.sinusoidal.get(freq = job['aspect'])},
    outputPath = outputPath
    )

if len(model.checkpoints) > 0:
    model.load_checkpoint('max')

observer = planetengine.observers.isobench.get()
observer.attach(model)

conditions = {
    'stopCondition': lambda: model.modeltime() > 0.3,
    # 'stopCondition': lambda: model.step() > 25,
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
