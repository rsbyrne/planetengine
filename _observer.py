from . import _built
from . import checkpoint
import os

class Observer(_built.Built):

    name = 'anonObs'

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

        self.path = ''

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

    def attach(self, system):

        assert hasattr(system, 'initials'), \
            "System must have initials set."

        builts = {
            'observer': self,
            'observed': {
                'system': system,
                'initials': system.initials
                }
            }

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
            dataCollectors = saveCollectors,
            builts = builts
            )

        self.system = system
        self.initials = system.initials
        self.builts = builts
        self.saveVars = saveVars
        self.figs = saveFigs
        self.collectors = saveCollectors
        self.checkpointer = checkpointer
        self.step = system.step
        self.modeltime = system.modeltime

    def attach_frame(self, frame):
        self.attach(frame.system)
        frame.observers.add(self)
        self.path = os.path.join(frame.path, self.name)

    def prompt(self, status = None):
        self._prompt()
        if status == 'checkpointing':
            self.checkpoint()

    def checkpoint(self, path = None, clear = True):
        if path is None:
            path = self.path
        self.checkpointer.checkpoint(path)
        if path == self.path:
            for collector in self.saveCollectors:
                collector.clear()
