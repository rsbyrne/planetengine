from . import _built
from . import checkpoint
from . import _frame
from . import _system
from . import mpi
import os

def load_observer(name, path, system = None):
    obsDir = os.path.join(path, name)
    print(obsDir)
    builts = _built.load_builtsDir(obsDir)
    loadObserver = builts['observer']
    if system is None:
        loadSystem = builts['observed']['system']
        loadInitials = builts['observed']['initials']
        loadSystem.initialise(loadInitials)
    else:
        if not isinstance(system, _system.System):
            raise Exception
        loadSystem = system
    loadObserver.attach(loadSystem)
    return loadObserver

def load_observers(path, system = None, return_dict = False):
    files = []
    if mpi.rank == 0:
        files = os.listdir(path)
    files = mpi.comm.bcast(files, root = 0)
    loadObservers = []
    for file in files:
        if file[:6] == 'peobs':
            loadObserver = load_observer(
                file,
                path,
                system
                )
            loadObservers.append(loadObserver)
    if return_dict:
        loadObservers = {
            loadObserver.instanceID: loadObserver \
                for loadObserver in loadObservers
            }
    return loadObservers

class Observer(_built.Built):

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

        self.path = ''
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
            frame.observers[self.name] = self
            path = frame.path
            system = frame.system
            initials = frame.initials
        elif isinstance(attachee, _system.System):
            path = '.'
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
            dataCollectors = saveCollectors,
            builts = builts
            )

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
        self.stamps = stamps
        self.instanceID = instanceID
        self.path = path

        self.attached = True

    def prompt(self, status = None):
        if not self.attached:
            raise Exception("Not yet attached.")
        self._prompt()
        if status == 'checkpointing':
            self.checkpoint()

    def checkpoint(self, path = None, clear = True):
        if not self.attached:
            raise Exception("Not yet attached.")
        if path is None:
            path = self.path
        checkpointPath = os.path.join(path, self.instanceID)
        self.checkpointer.checkpoint(checkpointPath)
        if path == self.path:
            for collector in self.saveCollectors:
                collector.clear()
