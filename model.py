from planetengine import paths
from planetengine import utilities
from planetengine.utilities import message
from planetengine.visualisation import QuickFig
from planetengine import frame
Frame = frame.Frame

def make_model(
        system,
        initials,
        outputPath = None,
        instanceID = None,
        ):
    builts = {
        'system': system,
        **initials
        }
    outFrame = frame.make_frame(
        Model,
        builts,
        outputPath,
        instanceID
        )
    return outFrame

def new_frame(*args, **kwargs):
    outFrame = Model(
        *args,
        **kwargs
        )
    return outFrame

class Model(Frame):

    prefix = 'pemod'
    framescript = __file__
    info = {}

    def __init__(self,
            builts,
            outputPath = None,
            instanceID = 'test',
            _autoarchive = True,
            _parentFrame = None,
            _is_child = False,
            _autobackup = True,
            ):

        system = builts['system']
        initials = {
            key: val for key, val in builts.items() \
                if not key == 'system'
            }

        if outputPath is None:
            outputPath = paths.defaultPath

        assert system.varsOfState.keys() == initials.keys()

        message("Building model...")

        step = 0
        modeltime = 0.

        inFrames = []
        for IC in initials.values():
            try:
                inFrames.append(IC.inFrame)
            except:
                pass

        analysers = []
        collectors = []
        fig = QuickFig(
            *[value for key, value in sorted(system.varsOfState.items())],
            style = 'smallblack',
            )
        figs = [fig]
        saveVars = system.varsOfState

        # SPECIAL TO MODEL
        self.system = system
        self.observers = set()
        self.initials = initials
        self.analysers = analysers

        # NECESSARY FOR FRAME CLASS:
        self.outputPath = outputPath
        self.instanceID = instanceID
        self.inFrames = inFrames
        self.step = step
        self.modeltime = modeltime
        self.saveVars = saveVars
        self.figs = figs
        self.collectors = collectors
        self.builts = builts

        # OVERRIDE FRAME CLASS:
        self._autobackup = _autobackup
        self._autoarchive = _autoarchive
        self._is_child = _is_child
        self._parentFrame = _parentFrame

        super().__init__()

    # METHODS NECESSARY FOR FRAME CLASS:

    def initialise(self):
        message("Initialising...")
        for varName, var in sorted(self.system.varsOfState.items()):
            self.initials[varName].apply(var)
        self.system.update()
        self.step = 0
        self.modeltime = 0.
        self.update()
        message("Initialisation complete!")

    def update(self):
        self.system.update()

    # METHODS NOT NECESSARY:

    def _prompt_observers(self, prompt):
        observerList = utilities.parallelise_set(
            self.observers
            )
        for observer in observerList:
            observer.prompt(prompt)

    def _post_checkpoint_hook(self):
        self._prompt_observers('checkpointing')

    def all_analyse(self):
        message("Analysing...")
        for analyser in self.analysers:
            analyser.analyse()
        message("Analysis complete!")

    def report(self):
        message(
            '\n' \
            + 'Step: ' + str(self.step) \
            + ', modeltime: ' + '%.3g' % self.modeltime
            )
        for fig in self.figs:
            fig.show()

    def iterate(self):
        assert not self._is_child, \
            "Cannot iterate child models independently."
        message("Iterating step " + str(self.step) + " ...")
        dt = self.system.iterate()
        self.step += 1
        self.modeltime += dt
        self._prompt_observers('iterated')
        message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step + steps
        self.traverse(lambda: self.step >= stopStep)

    def traverse(self, stopCondition,
            collectConditions = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            forge_on = False,
            ):

        if not type(collectConditions) is list:
            collectConditions = [collectConditions,]
            assert len(collectConditions) == len(self.collectors)

        if checkpointCondition():
            self.checkpoint()

        message("Running...")

        while not stopCondition():

            try:
                self.iterate()
                if checkpointCondition():
                    self.checkpoint()
                else:
                    for collector, collectCondition in zip(
                            self.collectors,
                            collectConditions
                            ):
                        if collectCondition():
                            collector.collect()
                if reportCondition():
                    self.report()

            except:
                if forge_on:
                    message("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        message("Done!")
        if checkpointCondition():
            self.checkpoint()
