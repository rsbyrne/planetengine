from . import paths
from . import utilities
from .utilities import message
from .visualisation import QuickFig
from . import _frame as frame
from .value import Value
from . import _system
from . import _observer

Frame = frame.Frame

def make_model(
        outputPath = None,
        instanceID = None,
        system = None,
        initials = None
        ):
    return frame.make_frame(
        Model,
        outputPath = outputPath,
        instanceID = instanceID,
        system = system,
        initials = initials
        )

load_model = frame.load_frame

class Model(Frame):

    prefix = 'pemod'
    framescript = __file__
    info = {'frameType': 'pemod'}

    def __init__(
            self,
            system = None,
            initials = None,
            outputPath = None,
            instanceID = None
            ):

        if outputPath is None:
            outputPath = paths.defaultPath

        if not isinstance(system, _system.System):
            raise Exception(
                "System must be an instance of 'system'; instead, type was " + str(type(system)) + "."
                )

        assert system.varsOfState.keys() == initials.keys()

        message("Building model...")

        step = system.step
        modeltime = system.modeltime

        analysers = []
        collectors = []
        figs = [system.fig]
        saveVars = system.varsOfState

        # SPECIAL TO MODEL
        self.system = system
        self.observers = {}
        self.initials = initials
        self.analysers = analysers

        builts = {'system': system, 'initials': initials}

        super().__init__(
            outputPath, # must be str
            instanceID, # must be str
            step, # must be Value
            modeltime, # must be Value
            saveVars, # dict of vars
            figs, # figs to save
            collectors,
            self.update,
            self.initialise,
            builts,
            self.info,
            self.framescript,
            )

    # METHODS NECESSARY FOR FRAME CLASS:

    def initialise(self):
        message("Initialising...")
        self.system.initialise(self.initials)
        message("Initialisation complete!")

    def update(self):
        message("Updating...")
        self.system.update()
        message("Updated.")

    # METHODS NOT NECESSARY:

    def _prompt_observers(self, prompt):
        for observerName, observer \
                in sorted(self.observers.items()):
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
            + 'Step: ' + str(self.step()) \
            + ', modeltime: ' + '%.3g' % self.modeltime()
            )
        for fig in self.figs:
            fig.show()

    def iterate(self):
        message("Iterating step " + str(self.step()) + " ...")
        self.system.iterate()
        self._prompt_observers('iterated')
        message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step() + steps
        self.traverse(lambda: self.step() >= stopStep)

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

    def _post_load_hook(self):
        self._load_observers()

    def _load_observers(self):
        loadObservers = _observer.load_observers(self.path)
        for loadObserver in loadObservers:
            self.observers[loadObserver.name] = loadObserver

### IMPORTANT!!! ###
frame.frameClasses[Model.prefix] = Model
