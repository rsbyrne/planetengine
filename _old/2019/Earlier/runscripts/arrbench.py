import os
import sys

import planetengine

JOBID = str(sys.argv[1])

localDir = os.path.dirname(__file__)
campaign = planetengine.campaign.Campaign(
    os.path.basename(localDir),
    os.path.dirname(localDir),
    __file__
    )

jobFilename = planetengine.campaign.JOBPREFIX + JOBID
job = campaign.fm.load_json(jobFilename, 'jobs')

outputPath = os.path.join(campaign.fm.path, 'out')

model = planetengine.model.make_model(
    planetengine.systems.arrhenius.get(res = 16, **job),
    {'temperatureField': planetengine.initials.sinusoidal.get()},
    outputPath = outputPath
    )

if len(model.checkpoints) > 0:
    model.load_checkpoint('max')

observer = planetengine.observers.arrbench.get()
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
