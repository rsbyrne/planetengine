import tarfile
import os
import shutil
import json
import copy
import glob

from . import paths
from . import utilities
from . import disk
from . import _built as builtModule
from .wordhash import wordhash as wordhashFn
from . import checkpoint
from .utilities import message
from .utilities import check_reqs
from .disk import load_json
from .disk import expose_tar
from .visualisation import QuickFig

from . import mpi

make_stamps = builtModule.make_stamps

frameClasses = {}

def make_frame(
        subFrameClass,
        outputPath = None,
        instanceID = None,
        **builts
        ):

    if outputPath is None:
        outputPath = paths.defaultPath

    stamps = make_stamps(builts)

    if instanceID is None:
        prefix = subFrameClass.prefix
        instanceID = prefix + '_' + stamps['all'][1]

    path = os.path.join(outputPath, instanceID)
    diskstate = disk.disk_state(path)

    if diskstate == 'clean':
        message("Making a new frame...")
        frame = subFrameClass(
            outputPath = outputPath,
            instanceID = instanceID,
            **builts
            )
    else:
        with disk.expose(instanceID, outputPath) as filemanager:
            assert stamps == filemanager.load_json('stamps')
            message("Preexisting model found! Loading...")
            frame = load_frame(
                instanceID,
                outputPath
                )

    return frame

def load_frame(
        instanceID = '',
        outputPath = None,
        loadStep = 0
        ):

    if outputPath is None:
        outputPath = paths.defaultPath

    with disk.expose(instanceID, outputPath) as filemanager:

        builts = filemanager.load_builtsDir('builts')
        info = filemanager.load_json('info')

        frameClass = frameClasses[info['frameType']]
        frame = frameClass(
            outputPath = outputPath,
            instanceID = instanceID,
            **builts
            )
        frame._post_load_hook()

    return frame

class Frame:

    blackhole = [0., 0.]
    prefix = 'pe'

    def __init__(
            self,
            outputPath, # must be str
            instanceID, # must be str
            step, # must be 'Value'
            modeltime, # must be 'Value'
            update,
            initialise,
            builts,
            info,
            framescript,
            saveVars = {},
            figs = [],
            collectors = []
            ):

        self.outputPath = outputPath
        self.instanceID = instanceID
        self.saveVars = saveVars
        self.step = step
        self.modeltime = modeltime
        self.figs = figs
        self.collectors = collectors
        self.update = update
        self.initialise = initialise
        self.builts = builts
        self.info = info
        self.framescript = framescript

        # check_reqs(self)

        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarname = self.instanceID + '.tar.gz'
        self.tarpath = os.path.join(self.outputPath, self.tarname)
        self.backupdir = os.path.join(self.outputPath, 'backup')
        self.backuppath = os.path.join(self.backupdir, self.instanceID)
        self.backuptarpath = os.path.join(self.backupdir, self.tarname)

        self.stamps = make_stamps(self.builts)

        self.checkpoints = []

        self.checkpointer = checkpoint.Checkpointer(
            step = self.step,
            modeltime = self.modeltime,
            saveVars = self.saveVars,
            figs = self.figs,
            collectors = self.collectors,
            builts = self.builts,
            info = self.info,
            framescript = self.framescript,
            instanceID = self.instanceID
            )

        self.initialise()

        self.find_checkpoints()

        self._post_init_hook()

        message("Frame built!")

    def reset(self):
        self.initialise()
        self.most_recent_checkpoint = None

    def all_collect(self):
        message("Collecting...")
        for collector in self.collectors:
            collector.collect()
        message("Collecting complete!")

    def all_clear(self):
        message("Clearing all data...")
        for collector in self.collectors:
            collector.clear()
        message("All data cleared!")

    def disk_state(self, path = None):
        if path is None:
            path = self.path
        return disk.disk_state(path)

    def expose(self, **kwargs):
        return disk.expose(
            self.instanceID,
            self.outputPath,
            **kwargs
            )

    def local_checkpoint(self, backup = False, archive = True):

        self._pre_checkpoint_hook()

        if self.step() in self.checkpoints:
            message("Checkpoint already exists! Skipping.")
        else:
            self.checkpointer.checkpoint(
                outputPath = self.outputPath,
                archive = archive,
                postFn = self._post_checkpoint_hook
                )

        self.most_recent_checkpoint = self.step()
        self.checkpoints.append(self.step())
        self.checkpoints = sorted(set(self.checkpoints))

        if backup:
            self.backup()

    def remote_checkpoint(self, path, backup = False, archive = True):
        self.checkpointer.checkpoint(
            outputPath = path,
            clear = False,
            archive = archive
            )

    def checkpoint(
            self,
            path = None,
            backup = False,
            archive = True
            ):

        self.all_collect()

        if path is None or path == self.path:
            self.local_checkpoint(backup, archive)
        else:
            self.remote_checkpoint(path, backup, archive)

    def load_checkpoint(self, loadStep):

        message("Loading checkpoint...")

        if loadStep == 'max':
            loadStep = max(self.checkpoints)
        elif loadStep == 'min':
            loadStep = min(self.checkpoints)
        elif loadStep == 'latest':
            loadStep = self.most_recent_checkpoint
        else:
            if not type(loadStep) == int:
                raise Exception

        if loadStep == self.step():
            message(
                "Already at step " + str(loadStep) + ": aborting load_checkpoint."
                )
        elif loadStep == 0:
            self.reset()
        else:
            stepStr = str(loadStep).zfill(8)
            with self.expose() as filemanager:
                filemanager.load_vars(self.saveVars, subPath = stepStr)
            self.step.value = loadStep
            self.modeltime.value = disk.load_json('modeltime', checkpointFile)
            self.update()

            message("Checkpoint successfully loaded!")

    def find_checkpoints(self):

        checkpoints_found = []
        if not self.disk_state() == 'clean':
            with self.expose() as filemanager:
                for directory in filemanager.directories:
                    if (directory.isdigit() and len(directory) == 8):
                        loadstamps = filemanager.load_json('stamps', directory)
                        assert loadstamps == self.stamps, \
                            "Bad checkpoint found! Aborting."
                        message("Found checkpoint: " + directory)
                        checkpoints_found.append(int(directory))

            checkpoints_found = sorted(list(set(checkpoints_found)))

    def _pre_checkpoint_hook(self):
        pass

    def _post_checkpoint_hook(self):
        pass

    def fork(self, extPath, return_frame = False):

        disk_state = self.disk_state()

        message("Forking model to new directory...")

        if disk_state == 'clean':
            message("No files to fork yet.")
            if return_frame:
                newframe = copy.deepcopy(self)
                newframe.outputPath = extPath
                return newframe
        else:
            if mpi.rank == 0:
                os.makedirs(extPath, exist_ok = True)
                assert os.path.isdir(extPath)
            newpath = os.path.join(
                extPath,
                self.instanceID
                )
            if disk_state == 'tar':
                if mpi.rank == 0:
                    if os.path.isfile(newpath):
                        os.remove(newpath)
                    shutil.copyfile(
                        self.tarpath,
                        newpath
                        )
                    assert os.path.isfile(newpath)
                if return_frame:
                    newframe = load_frame(
                        self.instanceID,
                        extPath,
                        loadStep = self.step()
                        )
                    return newframe
            else:
                if mpi.rank == 0:
                    if os.path.isdir(newpath):
                        shutil.rmtree(newpath)
                    shutil.copytree(
                        self.path,
                        newpath
                        )
                    assert os.path.isdir(newpath)

        message(
            "Model forked to directory: " + extPath
            )

    def backup(self):
        message("Making a backup...")
        self.fork(self.backupdir)
        message("Backup saved.")

    def recover(self):
        message("Reverting to backup...")

        # Should make this robust: force it to do a stamp check first

        disk_state = self.disk_state()

        if mpi.rank == 0:

            assert os.path.exists(self.backuppath) or os.path.exists(self.backuptarpath), \
                "No backup found!"
            assert not os.path.exists(self.backuppath) and os.path.exists(self.backuptarpath), \
                "Conflicting backups found!"

            if disk_state() == 'tar':
                os.remove(self.tarpath)
            else:
                shutil.rmtree(self.path)

            if os.path.exists(self.backuptarpath):
                shutil.copyfile(self.backuptarpath, self.tarpath)
            else:
                shutil.copytree(self.backuppath, self.path)

        self.checkpoints = self.find_checkpoints()

        self.load_checkpoint(min(self.checkpoints, key=lambda x:abs(x - self.step())))

        message("Reverted to backup.")

    def archive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            message("Making a local archive...")
        else:
            path = _path
            message("Making a remote archive...")

        disk.make_tar(path)

    def unarchive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            message("Unarchiving the local archive...")
        else:
            path = _path
            message("Unarchiving a remote archive...")

        disk.expose_tar(path)

    def try_archive(self):
        if self.disk_state() == 'dir':
            self.archive()
            return True
        return False

    def try_unarchive(self):
        if self.disk_state() == 'tar':
            self.unarchive()
            return True
        return False

    def _post_load_hook(self):
        pass

    def _post_init_hook(self):
        pass
