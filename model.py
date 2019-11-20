from . import paths
from . import utilities
from .utilities import message
from .visualisation import QuickFig
from . import _frame as frame
from .value import Value
from . import _system
from . import _observer
from . import disk

Frame = frame.Frame

def make_model(
        system = None,
        initials = None,
        instanceID = None,
        outputPath = None
        ):
    if initials is None:
        initials = system.initials
    return frame.make_frame(
        Model,
        system = system,
        initials = initials,
        instanceID = instanceID,
        outputPath = outputPath
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

        saveVars = system.varsOfState

        # SPECIAL TO MODEL
        self.system = system
        self.observers = {}
        self.initials = initials

        self.status = "idle"

        builts = {'system': system, 'initials': initials}

        super().__init__(
            outputPath, # must be str
            instanceID, # must be str
            step, # must be Value
            modeltime, # must be Value
            self.update,
            self.initialise,
            builts,
            self.info,
            self.framescript,
            saveVars, # dict of vars
            # figs, # figs to save
            # collectors,
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

    def report(self):
        for observerName, observer \
                in sorted(self.observers.items()):
            message(observerName + ':')
            observer.report()

    def iterate(self):
        message("Iterating step " + str(self.step()) + " ...")
        self.system.iterate()
        self._prompt_observers('iterated')
        message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step() + steps
        self.traverse(lambda: self.step() >= stopStep)

    def traverse(self,
            stopCondition,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            forge_on = False,
            ):

        self.status = 'pre-traverse'

        if checkpointCondition():
            self.checkpoint()

        message("Running...")

        while not stopCondition():

            self.status = 'traverse'

            try:
                self.iterate()
                if checkpointCondition():
                    self.checkpoint()
                if reportCondition():
                    self.report()

            except:
                if forge_on:
                    message("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, \
                        "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        self.status = 'post-traverse'

        message("Done!")
        if checkpointCondition():
            self.checkpoint()

        self.status = 'idle'

    def _post_load_hook(self):
        self._load_observers()

    def _load_observers(self):
        with disk.expose(self.instanceID, self.outputPath) as filemanager:
            loadObservers = _observer.load_observers(
                filemanager.path,
                self.system
                )
        for loadObserver in loadObservers:
            self.observers[loadObserver.instanceID] = loadObserver

### IMPORTANT!!! ###
frame.frameClasses[Model.prefix] = Model
