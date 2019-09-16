from . import paths
from . import utilities
from .utilities import message
from .visualisation import QuickFig
from . import _frame as frame
from .value import Value
from . import _system

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

# def new_frame(*args, **kwargs):
#     outFrame = Model(
#         *args,
#         **kwargs
#         )
#     return outFrame

class Model(Frame):

    prefix = 'pemod'
    framescript = __file__
    info = {'frameType': 'pemod'}

    def __init__(
            self,
            system = None,
            initials = None,
            outputPath = None,
            instanceID = 'test',
            _autoarchive = True,
            _autobackup = True
            ):

        if outputPath is None:
            outputPath = paths.defaultPath

        if not isinstance(system, _system.System):
            raise Exception(
                "System must be an instance of 'system'; instead, type was " + str(type(system)) + "."
                )

        assert system.varsOfState.keys() == initials.keys()

        message("Building model...")

        step = Value(0)
        modeltime = Value(0.)

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

        # OVERRIDE FRAME CLASS:
        self._autobackup = _autobackup
        self._autoarchive = _autoarchive

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
        for varName, var in sorted(self.system.varsOfState.items()):
            self.initials[varName].apply(var)
        self.update()
        self.step.value = 0
        self.modeltime.value = 0.
        message("Initialisation complete!")

    def update(self):
        message("Updating...")
        self.system.update()
        message("Updated.")

    # METHODS NOT NECESSARY:

    def _prompt_observers(self, prompt):
        ### DEBUGGING ###
        pass
        # observerList = utilities.parallelise_set(
        #     self.observers
        #     )
        # for observer in observerList:
        #     observer.prompt(prompt)

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
        dt = self.system.iterate()
        self.step.value += 1
        self.modeltime.value += dt
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

### IMPORTANT!!! ###
frame.frameClasses[Model.prefix] = Model
