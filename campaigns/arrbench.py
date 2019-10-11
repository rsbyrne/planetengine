import planetengine
campaign = planetengine.campaign
disk = planetengine.disk

def build(*args, **kwargs):
    built = ArrBench(*args, **kwargs)
    return built

suites = {
    'light': lambda: planetengine.suite.suite_list({
        'f': [0.1, 0.5, 0.9],
        'eta0': [1., 1e2, 1e4],
        'Ra': [1e4, 1e5, 1e6],
        'res': 16
        }),
    'default': lambda: planetengine.suite.suite_list({
        'f': [round(x / 10., 1) for x in range(1, 11)],
        'eta0': [round(10.**(x / 2.), 0) for x in range(2, 12)],
        'Ra': [round(10.**(x / 2.), 0) for x in range(6, 16)],
        'res': 32
        })
    }

class ArrBench(campaign.Campaign):

    name = 'arrbench'
    script = __file__

    def __init__(
            self,
            *args,
            name = None,
            path = None,
            suite = [],
            **kwargs
            ):

        if type(suite) == str:
            suite = suites[suite]()

        ### HOUSEKEEPING: IMPORTANT! ###

        inputs = locals().copy()

        def _run(**kwargs):
            model = planetengine.model.make_model(
                planetengine.systems.arrhenius.build(**kwargs),
                {'temperatureField': planetengine.initials.sinusoidal.build()},
                outputPath = self.fm.directories['out']['.']
                )
            if len(model.checkpoints) > 0:
                model.load_checkpoint('max')
            observer = planetengine.observers.arrbench.build()
            observer.attach(model)
            conditions = {
                'stopCondition': lambda: model.modeltime() > 0.3,
                'stopCondition': lambda: model.step() > 3,
                'checkpointCondition': lambda: any([
                    model.status == 'pre-traverse',
                    model.step() % 1000 == 0,
                    model.status == 'post-traverse',
                    ]),
                }
            try:
                model.traverse(**conditions)
                return True
            except:
                return False

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


        self.add_jobs(suite)
