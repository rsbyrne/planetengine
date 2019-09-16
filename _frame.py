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
    tarpath = path + '.tar.gz'

    directory_state = ''

    if mpi.rank == 0:

        if os.path.isdir(path):
            if os.path.isfile(tarpath):
                raise Exception(
                    "Cannot combine model directory and tar yet."
                    )
            else:
                directory_state = 'directory'
        elif os.path.isfile(tarpath):
            directory_state = 'tar'
        else:
            directory_state = 'clean'

    directory_state = mpi.comm.bcast(directory_state, root = 0)
    mpi.comm.barrier()

    if directory_state == 'tar':
        if mpi.rank == 0:
            with tarfile.open(tarpath) as tar:
                tar.extract('stamps.json', path)
        # mpi.barrier()
        loadstamps = disk.load_json('stamps', path)
        if mpi.rank == 0:
            shutil.rmtree(path)
        # mpi.barrier()
        assert loadstamps == stamps

    if not directory_state == 'clean':
        message("Preexisting model found! Loading...")
        frame = load_frame(
            outputPath,
            instanceID
            )
    else:
        message("Making a new frame...")
        frame = subFrameClass(
            outputPath = outputPath,
            instanceID = instanceID,
            **builts
            )

        frame._post_init_hook()


    return frame

def load_frame(
        outputPath = None,
        instanceID = '',
        loadStep = 0
        ):
    '''
    Creates a new 'model' instance attached to a pre-existing
    model directory. LoadStep can be an integer corresponding
    to a previous checkpoint step, or can be the string 'max'
    which loads the highest stable checkpoint available.
    '''

    if outputPath is None:
        outputPath = paths.defaultPath

    # Check that target directory is not inside
    # another planetengine directory:

    if mpi.rank == 0:
        if os.path.isfile(
                os.path.join(outputPath, 'stamps.json')
                ):
            raise Exception
    # mpi.barrier()

    path = os.path.join(outputPath, instanceID)

    expose_tar(path)

    builts = builtModule.load_builtsDir(path)

    info = disk.load_json('info', path)

    frameClass = frameClasses[info['frameType']]

    frame = frameClass(
        outputPath = outputPath,
        instanceID = instanceID,
        **builts
        )

    frame._post_load_hook()

    return frame

class Frame:

    _autobackup = True
    _autoarchive = True
    blackhole = [0., 0.]

    def __init__(
            self,
            outputPath, # must be str
            instanceID, # must be str
            step, # must be 'Value'
            modeltime, # must be 'Value'
            saveVars, # dict of vars
            figs, # figs to save
            collectors,
            update,
            initialise,
            builts,
            info,
            framescript,
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

        self.archived = False #_isArchived

        self.checkpoints = []

        self.checkpointer = checkpoint.Checkpointer(
            step = self.step,
            modeltime = self.modeltime,
            saveVars = self.saveVars,
            figs = self.figs,
            dataCollectors = self.collectors,
            builts = self.builts,
            info = self.info,
            framescript = self.framescript
            )

        self.initialise()

        self.find_checkpoints()

        if all([
                self._autoarchive,
                not self.archived
                ]):
            self.archive()

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

    def checkpoint(self, path = None):

        self.all_collect()

        if path is None or path == self.path:

            if self.archived:
                self.unarchive()

            self._pre_checkpoint_hook()

            path = self.path

            if self.step() in self.checkpoints:
                message("Checkpoint already exists! Skipping.")
            else:
                self.checkpointer.checkpoint(path)

            self.all_clear()

            self.most_recent_checkpoint = self.step()
            self.checkpoints.append(self.step())
            self.checkpoints = sorted(set(self.checkpoints))

            # CHECKPOINT OBSERVERS!!!
            self._post_checkpoint_hook()

            if self._autoarchive:
                self.archive()

            if self._autobackup:
                self.backup()

        else:

            self.checkpointer.checkpoint(path)

    def load_checkpoint(self, loadStep):

        message("Loading checkpoint...")

        if loadStep == 'max':
            loadStep = max(self.checkpoints)
        elif loadStep == 'min':
            loadStep = min(self.checkpoints)
        elif loadStep == 'latest':
            loadStep = self.most_recent_checkpoint

        if loadStep == self.step():
            message(
                "Already at step " + str(loadStep) + ": aborting load_checkpoint."
                )

        elif loadStep == 0:
            self.reset()

        else:

            if self.archived:
                self.unarchive()

            stepStr = str(loadStep).zfill(8)

            checkpointFile = os.path.join(self.path, stepStr)

            disk.varsOnDisk(
                self.saveVars,
                checkpointFile,
                'load',
                self.blackhole
                )

            self.step.value = loadStep

            self.modeltime.value = disk.load_json('modeltime', checkpointFile)

            self.update()

            if self._autoarchive:
                self.archive()

            message("Checkpoint successfully loaded!")

    def find_checkpoints(self):

        path = os.path.join(self.outputPath, self.instanceID)
        stamps = make_stamps(self.builts)
        checkpoints_found = []

        directories = []
        if mpi.rank == 0:
            directories = glob.glob(path + '/*/')
        directories = mpi.comm.bcast(directories, root = 0)
        mpi.comm.barrier()

        for directory in directories:
            basename = os.path.basename(directory[:-1])
            if (basename.isdigit() and len(basename) == 8):
                loadstamps = disk.load_json('stamps', directory)
                assert loadstamps == stamps, \
                    "Bad checkpoint found! Aborting."
                message("Found checkpoint: " + basename)
                checkpoints_found.append(int(basename))
        checkpoints_found = sorted(list(set(checkpoints_found)))

        self.checkpoints = checkpoints_found

    def _pre_checkpoint_hook(self):
        pass

    def _post_checkpoint_hook(self):
        pass

    def fork(self, extPath, return_frame = False):

        message("Forking model to new directory...")

        hardFork = False

        if mpi.rank == 0:
            os.makedirs(extPath, exist_ok = True)
            assert os.path.isdir(extPath)
        # mpi.barrier()

        if self.archived:

            newpath = os.path.join(
                extPath,
                self.tarname
                )

            if mpi.rank == 0:
                shutil.copyfile(
                    self.tarpath,
                    newpath
                    )
            # mpi.barrier()

            message(
                "Model forked to directory: " + extPath
                )

            hardFork = True

        else:

            if self.archived:
                self.unarchive()

            pathexists = False
            if mpi.rank == 0:
                pathexists = os.path.isdir(self.path)
            pathexists = mpi.comm.bcast(pathexists, root = 0)
            # mpi.barrier()

            if pathexists:

                newpath = os.path.join(
                    extPath,
                    self.instanceID
                    )

                if mpi.rank == 0:
                    shutil.copytree(
                        self.path,
                        newpath
                        )
                # mpi.barrier()

                message(
                    "Model forked to directory: " + extPath + self.instanceID
                    )

                if self._autoarchive:
                    self.archive()
                    self.archive(newpath)

                hardFork = True

            else:

                message("No files to fork yet.")

                hardFork = False

        if return_frame:

            if hardFork:
                message(
                    "Loading newly forked frame at current model step: "
                    )
                newframe = load_frame(extPath, self.instanceID, loadStep = self.step())
                message(
                    "Loaded newly forked frame."
                    )
            else:
                message(
                    "Returning a copy of the current class object \
                    with a new outputPath."
                    )
                newframe = copy.deepcopy(self)
                newframe.outputPath = extPath

            return newframe

    def backup(self):
        message("Making a backup...")
        self.fork(self.backupdir)
        message("Backup saved.")

    def recover(self):
        message("Reverting to backup...")

        # Should make this robust: force it to do a stamp check first

        backup_archived = False

        if mpi.rank == 0:

            assert os.path.exists(self.backuppath) or os.path.exists(self.backuptarpath), \
                "No backup found!"
            assert not os.path.exists(self.backuppath) and os.path.exists(self.backuptarpath), \
                "Conflicting backups found!"

            if self.archived:
                os.remove(self.tarpath)
            else:
                shutil.rmtree(self.path)

            if os.path.exists(self.backuptarpath):
                backup_archived = True
                shutil.copyfile(self.backuptarpath, self.tarpath)
            else:
                shutil.copytree(self.backuppath, self.path)

        backup_archived = mpi.comm.bcast(backup_archived, root = 0)
        mpi.comm.barrier()

        was_archived = self.archived
        if backup_archived:
            self.archived = True
            self.unarchive()

        self.checkpoints = self.find_checkpoints()

        self.load_checkpoint(min(self.checkpoints, key=lambda x:abs(x - self.step())))

        if was_archived:
            self.archive()

        message("Reverted to backup.")

    def branch(self, extPath, return_frame = False, archive_remote = True):
        newpath = os.path.join(extPath, self.instanceID)
        self.checkpoint(newpath)
        self.archive(newpath)
        if return_frame:
            newframe = load_frame(extPath, self.instanceID)
            return newframe

    def archive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            tarpath = self.tarpath
            localArchive = True
            message("Making a local archive...")
        else:
            path = _path
            tarpath = path + '.tar.gz'
            localArchive = False
            message("Making a remote archive...")

        isdir = False
        isfile = False
        if mpi.rank == 0:
            isdir = os.path.isdir(path)
            isfile = os.path.isfile(path)
        isdir = mpi.comm.bcast(isdir, root = 0)
        isfile = mpi.comm.bcast(isfile, root = 0)
        if not isdir:
            message("Nothing to archive yet!")
            return None
        if isfile:
            message("Already archived!")
            return None

        ### INDEV ###
        # if hasattr(self, '_parentFrame'):
        #     if localArchive:
        #         self._parentFrame.archive()
        #         return None

        message("Archiving...")

        if mpi.rank == 0:

            with tarfile.open(tarpath, 'w:gz') as tar:
                tar.add(path, arcname = '')

            assert os.path.isfile(tarpath), \
                "The archive should have saved, but we can't find it!"

            message("Deleting model directory...")
            shutil.rmtree(path)
            assert not os.path.isdir(path), \
                "The directory should have been deleted, but it's still there!"
            message("Model directory deleted.")

        # mpi.barrier()

        if localArchive:
            self.archived = True

        message("Archived!")

    def unarchive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            tarpath = self.tarpath
            localArchive = True
            message("Unarchiving the local archive...")
        else:
            path = _path
            tarpath = path + '.tar.gz'
            localArchive = False
            message("Unarchiving a remote archive...")

        isdir = False
        isfile = False
        if mpi.rank == 0:
            isdir = os.path.isdir(path)
            isfile = os.path.isfile(path)
        isdir = mpi.comm.bcast(isdir, root = 0)
        isfile = mpi.comm.bcast(isfile, root = 0)
        if isdir:
            message("Already unarchived!")
            return None
        if not isfile:
            message("Nothing to unarchive yet!")
            return None

        ### INDEV ###
        # if hasattr(self, '_parentFrame'):
        #     if localArchive:
        #         self._parentFrame.unarchive()
        #         return None

        message("Unarchiving...")

        if _path is None or _path == self.path:
            path = self.path
            localArchive = True
            message("Unarchiving the local archive...")
        else:
            path = _path
            localArchive = False
            message("Unarchiving a remote archive...")

        disk.expose_tar(path)

        # mpi.barrier()

        if localArchive:
            self.archived = False

        message("Unarchived!")

    def _post_load_hook(self):
        pass

    def _post_init_hook(self):
        pass
