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

        if os.path.isdir(path) and os.path.isfile(tarpath):
                raise Exception(
                    "Cannot combine model directory and tar yet."
                    )
        if os.path.isdir(path):
            directory_state = 'directory'
        elif os.path.isfile(tarpath):
            directory_state = 'tar'
        else:
            directory_state = 'clean'

    directory_state = mpi.comm.bcast(directory_state, root = 0)
    # mpi.comm.barrier()

    if directory_state == 'tar':
        if mpi.rank == 0:
            with tarfile.open(tarpath) as tar:
                tar.extract('stamps.json', path)
            assert os.path.isfile(os.path.join(path, 'stamps.json'))
        loadstamps = disk.load_json('stamps', path)
        if mpi.rank == 0:
            shutil.rmtree(path)
            assert not os.path.isdir(path)
        assert loadstamps == stamps

    if not directory_state == 'clean':
        message("Preexisting model found! Loading...")
        frame = load_frame(
            instanceID,
            outputPath
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
        instanceID = '',
        outputPath = None,
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

    if disk.disk_state(path) == 'tar':
        expose_tar(path)
        was_archived = True
    else:
        was_archived = False

    builts = builtModule.load_builtsDir(path)

    info = disk.load_json('info', path)

    frameClass = frameClasses[info['frameType']]

    frame = frameClass(
        outputPath = outputPath,
        instanceID = instanceID,
        **builts
        )

    frame._post_load_hook()

    if was_archived:
        frame.archive()

    return frame

class Frame:

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

    def checkpoint(
            self,
            path = None,
            backup = True,
            archive = None
            ):

        disk_state = self.disk_state()
        if archive is None:
            if disk_state == 'tar':
                archive = True
            elif disk_state == 'clean':
                archive = True
            else:
                archive = False

        self.all_collect()

        if path is None or path == self.path:

            self._pre_checkpoint_hook()

            self.try_unarchive()

            path = self.path

            if self.step() in self.checkpoints:
                message("Checkpoint already exists! Skipping.")
            else:
                self.checkpointer.checkpoint(path)

            # self.all_clear()

            self.most_recent_checkpoint = self.step()
            self.checkpoints.append(self.step())
            self.checkpoints = sorted(set(self.checkpoints))

            # CHECKPOINT OBSERVERS!!!
            self._post_checkpoint_hook()

            if archive:
                self.try_archive()

            if backup:
                self.backup()

        else:

            self.checkpointer.checkpoint(path, clear = False)
            if archive:
                self.archive(path)

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

            was_archived = self.try_unarchive()

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

            if was_archived:
                self.try_archive()

            message("Checkpoint successfully loaded!")

    def find_checkpoints(self):

        was_archived = self.try_unarchive()

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

        if was_archived:
            self.archive()

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

        disk_state = self.disk_state()

        if disk_state == 'tar':

            newpath = os.path.join(
                extPath,
                self.tarname
                )

            if mpi.rank == 0:
                shutil.copyfile(
                    self.tarpath,
                    newpath
                    )
                assert os.path.isfile(newpath)
            # mpi.barrier()

            message(
                "Model forked to directory: " + extPath
                )

            hardFork = True

        elif disk_state == 'dir':

            newpath = os.path.join(
                extPath,
                self.instanceID
                )

            if mpi.rank == 0:
                shutil.copytree(
                    self.path,
                    newpath
                    )

            message(
                "Model forked to directory: " + extPath + self.instanceID
                )

            hardFork = True

        else:

            message("No files to fork yet.")

            hardFork = False

        if return_frame:

            if hardFork:
                message(
                    "Loading newly forked frame at current model step: "
                    )
                newframe = load_frame(self.instanceID, extPath, loadStep = self.step())
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
                backup_archived = True
                shutil.copyfile(self.backuptarpath, self.tarpath)
            else:
                shutil.copytree(self.backuppath, self.path)

        backup_archived = mpi.comm.bcast(backup_archived, root = 0)

        was_archived = disk_state == 'tar'
        if backup_archived:
            self.try_unarchive()

        self.checkpoints = self.find_checkpoints()

        self.load_checkpoint(min(self.checkpoints, key=lambda x:abs(x - self.step())))

        if was_archived:
            self.try_archive()

        message("Reverted to backup.")

    def branch(self, extPath, return_frame = False, archive_remote = True):
        newpath = os.path.join(extPath, self.instanceID)
        self.checkpoint(newpath)
        self.archive(newpath)
        if return_frame:
            newframe = load_frame(self.instanceID, extPath)
            return newframe

    def archive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            message("Making a local archive...")
        else:
            path = _path
            message("Making a remote archive...")

        assert self.disk_state(path) == 'dir'

        message("Archiving...")

        if mpi.rank == 0:
            with tarfile.open(path + '.tar.gz', 'w:gz') as tar:
                tar.add(path, arcname = '')
            assert os.path.isfile(path + '.tar.gz'), \
                "The archive should have been created, but it wasn't!"
            shutil.rmtree(path)
            assert not os.path.isdir(path), \
                "The directory should have been deleted, but it's still there!"

        assert self.disk_state(path) == 'tar'

        message("Archived!")

    def unarchive(self, _path = None):

        if _path is None or _path == self.path:
            path = self.path
            message("Unarchiving the local archive...")
        else:
            path = _path
            message("Unarchiving a remote archive...")

        disk.expose_tar(path)

        message("Unarchived!")

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
