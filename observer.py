from .utilities import Grouper
from .utilities import hashstamp
from .wordhash import wordhash as wordhashFn
from .checkpoint import Checkpointer
from .frame import _scripts_and_stamps
import underworld as uw

class Observer:

    figs = []
    collectors = []

    def __init__(
            self,
            system,
            initials,
            scriptlist,
            **kwargs
            ):

        obsInp = kwargs

        scripts = {}
        for index, script in enumerate(scriptlist):
            scriptname = 'observerscript_' + str(index)
            scripts[scriptname] = script

        # Making stamps and stuff

        _model_inputs, _model_stamps, _model_hashID, _model_scripts = \
            _scripts_and_stamps(system, initials)

        stamps = {}
        if uw.mpi.rank == 0:
            stamps = {
                'inputs': hashstamp(obsInp),
                'scripts': hashstamp(
                    [open(script) for scriptname, script \
                        in sorted(scripts.items())]
                    )
                }
            for stampKey, stampVal in stamps.items():
                stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
            stamps['model_stamps'] = [_model_hashID, _model_stamps]
        stamps = uw.mpi.comm.bcast(stamps, root = 0)

        scripts.update(_model_scripts)
        inputs = {
            'obsInp': obsInp,
            **_model_inputs,
            }

        # Making the checkpointer:

        checkpointer = Checkpointer(
            stamps = stamps,
            step = system.step,
            modeltime = system.modeltime,
            figs = self.figs,
            dataCollectors = self.collectors,
            scripts = scripts,
            inputs = inputs
            )

        self.checkpointer = checkpointer
        self.inputs = inputs
        self.scripts = scripts
        self.stamps = stamps
        self.system = system
        self.initials = initials
        self.step = system.step
        self.modeltime = system.modeltime

    def checkpoint(self, path):
        self.checkpointer.checkpoint(path)

    def prompt(self):
        pass
