import everest
from . import system
from . import mpi
from .utilities import message
import os

class Observer(everest.built.Built):

    name = 'anonObs'
    prefix = 'peobs'

    def __init__(
            self,
            args,
            kwargs,
            inputs,
            script,
            _attach,
            _prompt,
            ):

        self._prompt = _prompt
        self._attach = _attach

        self.frame = None
        self.system = None
        self.initials = None
        self.attached = False
        self.instanceID = None

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

    def attach(self, attachee):

        if isinstance(attachee, _frame.Frame):
            frame = attachee
            outputPath = frame.path
            system = frame.system
            initials = frame.initials
        elif isinstance(attachee, system.System):
            outputPath = None
            frame = None
            system = attachee
            if not hasattr(system, 'initials'):
                raise Exception("System must have initials set.")
            initials = system.initials

        builts = {
            'observer': self,
            'observed': {
                'system': system,
                'initials': system.initials
                }
            }
        stamps = _built.make_stamps(builts)
        instanceID = self.prefix + '_' + stamps['all'][1]

        saveVars, saveFigs, saveCollectors = \
            self._attach(system)

        for sub in self.subs:
            sub_saveVars, sub_saveFigs, sub_saveCollectors = \
                sub._attach(system)
            saveVars.extend(sub_saveVars)
            saveFigs.append(sub_saveFigs)
            saveCollectors.append(sub_saveCollectors)

        checkpointer = checkpoint.Checkpointer(
            step = system.step,
            modeltime = system.modeltime,
            saveVars = saveVars,
            figs = saveFigs,
            collectors = saveCollectors,
            builts = builts,
            instanceID = instanceID
            )

        if isinstance(attachee, _frame.Frame):
            attachee.observers[instanceID] = self

        self.frame = frame
        self.system = system
        self.initials = system.initials
        self.builts = builts
        self.saveVars = saveVars
        self.figs = saveFigs
        self.collectors = saveCollectors
        self.checkpointer = checkpointer
        self.step = system.step
        self.modeltime = system.modeltime
        self.instanceID = instanceID
        self.outputPath = outputPath

        self.attached = True

    def prompt(self, status = None):
        message("Observer prompted.")
        if not self.attached:
            raise Exception("Not yet attached.")
        self._prompt()
        if status == 'checkpointing':
            self.checkpoint()

    def checkpoint(self):
        message("Observer checkpointing...")
        if not self.attached:
            raise Exception("Not yet attached.")
        self.checkpointer.checkpoint(
            outputPath = self.outputPath
            )
        message("Observer checkpointed.")
