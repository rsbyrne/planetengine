from ._frametools import *

class Frame:

    _required_attributes = {
        'outputPath', # must be str
        'instanceID', # must be str
        'inFrames', # must be list of Frames objects
        'step', # must be int
        'modeltime', # must be float
        'saveVars', # dict of vars
        'figs', # figs to save
        'collectors',
        'update',
        'initialise',
        'builts',
        'info'
        }

    _autobackup = True
    _autoarchive = True
    _is_child = False
    _parentFrame = None
    blackhole = [0., 0.]

    def __init__(self):

        check_reqs(self)

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
            step = lambda: self.step,
            modeltime = lambda: self.modeltime,
            saveVars = self.saveVars,
            figs = self.figs,
            dataCollectors = self.collectors,
            builts = self.builts,
            info = self.info,
            inFrames = self.inFrames,
            )

        self.initialise()

        self.find_checkpoints()

        for inFrame in self.inFrames:
            # CIRCULAR REFERENCE:
            inFrame._parentFrame = self

        if all([
                self._autoarchive,
                not self.archived,
                not self._is_child
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

            if self.step in self.checkpoints:
                message("Checkpoint already exists! Skipping.")
            else:
                self.checkpointer.checkpoint(path)

            self.all_clear()

            self.most_recent_checkpoint = self.step
            self.checkpoints.append(self.step)
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

        if loadStep == self.step:
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

            self.step = loadStep

            modeltime = 0.
            if uw.mpi.rank == 0:
                modeltime_filepath = os.path.join(
                    checkpointFile,
                    'modeltime.json'
                    )
                with open(modeltime_filepath, 'r') as file:
                    modeltime = json.load(file)
            modeltime = uw.mpi.comm.bcast(modeltime, root = 0)

            self.modeltime = modeltime

            self.update()

            if self._autoarchive and not self._is_child:
                self.archive()

            message("Checkpoint successfully loaded!")

    def find_checkpoints(self):
        path = os.path.join(self.outputPath, self.instanceID)
        stamps = make_stamps(self.builts)
        checkpoints_found = []
        if uw.mpi.rank == 0:
            for directory in glob.glob(path + '/*/'):
                basename = os.path.basename(directory[:-1])
                if (basename.isdigit() and len(basename) == 8):
                    with open(os.path.join(directory, 'stamps.json')) as json_file:
                        loadstamps = json.load(json_file)
                    assert loadstamps == stamps, \
                        "Bad checkpoint found! Aborting."
                    message("Found checkpoint: " + basename)
                    checkpoints_found.append(int(basename))
            checkpoints_found = sorted(list(set(checkpoints_found)))
        checkpoints_found = uw.mpi.comm.bcast(checkpoints_found, root = 0)
        self.checkpoints = checkpoints_found

    def _pre_checkpoint_hook(self):
        pass

    def _post_checkpoint_hook(self):
        pass

    def fork(self, extPath, return_frame = False):

        message("Forking model to new directory...")

        if uw.mpi.rank == 0:

            os.makedirs(extPath, exist_ok = True)

            if self.archived and not self._is_child:
                newpath = os.path.join(
                    extPath,
                    self.tarname
                    )
                shutil.copyfile(
                    self.tarpath,
                    newpath
                    )
                message(
                    "Model forked to directory: " + extPath
                    )
                hardFork = True
            else:
                if self.archived:
                    self.unarchive()
                if os.path.isdir(self.path):
                    newpath = os.path.join(
                        extPath,
                        self.instanceID
                        )
                    shutil.copytree(
                        self.path,
                        newpath
                        )
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
                newframe = load_frame(extPath, self.instanceID, loadStep = self.step)
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

        if uw.mpi.rank == 0:

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

        backup_archived = uw.mpi.comm.bcast(backup_archived, root = 0)

        was_archived = self.archived
        if backup_archived:
            self.archived = True
            self.unarchive()

        self.checkpoints = self.find_checkpoints()

        self.load_checkpoint(min(self.checkpoints, key=lambda x:abs(x - self.step)))

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

        if not os.path.isdir(path):
            message("Nothing to archive yet!")
            return None
        if os.path.isfile(tarpath):
            message("Already archived!")
            return None
        if self._is_child:
            message("Bumping archive call up to parent...")
            self._parentFrame.archive(_path)

        assert self.archived == False

        message("Archiving...")

        if uw.mpi.rank == 0:

            with tarfile.open(tarpath, 'w:gz') as tar:
                tar.add(path, arcname = '')

            assert os.path.isfile(tarpath), \
                "The archive should have saved, but we can't find it!"

            message("Deleting model directory...")
            shutil.rmtree(path)
            message("Model directory deleted.")

        if localArchive:
            self._set_inner_archive_status(True)

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

        if os.path.isdir(path):
            message("Already unarchived!")
            return None
        if not os.path.isfile(tarpath):
            message("Nothing to unarchive yet!")
            return None
        if self._is_child:
            message("Bumping unarchive call up to parent...")
            self._parentFrame.archive(_path)
            return None

        assert self.archived == True

        message("Unarchiving...")

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

        if uw.mpi.rank == 0:
            assert not os.path.isdir(path), \
                "Destination directory already exists!"
            assert os.path.isfile(tarpath), \
                "No archive to unpack!"

            with tarfile.open(tarpath) as tar:
                tar.extractall(path)

            assert os.path.isdir(path), \
                "The model directory doesn't appear to exist."

            message("Deleting archive...")

            os.remove(tarpath)

            message("Model directory deleted.")

        if localArchive:
            self._set_inner_archive_status(False)

        message("Unarchived!")

    def _set_inner_archive_status(self, status):
        self.archived = status
        for inFrame in self.inFrames:
            if inFrame._is_child:
                inFrame._set_inner_archive_status(status)
