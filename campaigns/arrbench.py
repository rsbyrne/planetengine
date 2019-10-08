from planetengine import campaign
from planetengine import disk

def build(*args, **kwargs):
    built = ArrBench(*args, **kwargs)
    return built

class ArrBench(campaign.Campaign):

    name = 'arrbench'
    script = __file__

    def __init__(
            self,
            *args,
            name = None,
            path = None,
            **kwargs
            ):

        ### HOUSEKEEPING: IMPORTANT! ###

        inputs = locals().copy()

        def _run(job):
            model = planetengine.model.make_model(
                planetengine.systems.arrhenius.build(res = 16, **job),
                {'temperatureField': planetengine.initials.sinusoidal.build()},
                outputPath = self.fm.directories['out']['.']
                )
            if len(model.checkpoints) > 0:
                model.load_checkpoint('max')
            observer = planetengine.observers.arrbench.build()
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

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script,
            _run = _run,
            name = name,
            path = path,
            # _pre_update = _pre_update,
            # _post_update = _post_update,
            )

### CORE FUNCTIONALITY: IMPORTANT! ###
import sys
if len(sys.argv) > 1:
    if campaign.JOBPREFIX in str(sys.argv[1]):
        JOBFILENAME = str(sys.argv[1])
        job = disk.load_json(JOBFILENAME)
        print(job)
        campaignObj = build()
        campaignObj.run(job)
