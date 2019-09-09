import underworld as uw
import tarfile
import os
import shutil
import json
import copy
import glob

from . import paths
from . import utilities
from . import disk
from .wordhash import wordhash as wordhashFn
from . import checkpoint
from .utilities import message
from .utilities import check_reqs
from .visualisation import QuickFig

def expose_tar(path):

    tarpath = path + '.tar.gz'

    print(path)

    if uw.mpi.rank == 0:
        assert os.path.isdir(path) or os.path.isfile(tarpath), \
            "No model found at that directory!"

    if uw.mpi.rank == 0:
        if os.path.isfile(tarpath):
            assert not os.path.isdir(path), \
                "Conflicting archive and directory found."
            message("Tar found - unarchiving...")
            with tarfile.open(tarpath) as tar:
                tar.extractall(path)
            message("Unarchived.")
            assert os.path.isdir(path), \
                "Archive contained the wrong model file somehow."
            os.remove(tarpath)

def load_json(jsonName, path):
    filename = jsonName + '.json'
    jsonDict = {}
    if uw.mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            jsonDict = json.load(json_file)
    jsonDict = uw.mpi.comm.bcast(jsonDict, root = 0)
    return jsonDict

load_inputs = load_json

def load_jsons(jsonNames, path):
    jsons = {}
    if uw.mpi.rank == 0:
        for jsonName in jsonNames:
            jsons[jsonName] = load_json(
                jsonName,
                path
                )
    jsons = uw.mpi.comm.bcast(jsons, root = 0)
    return jsons

def load_builts(names, path):
    builtsDir = os.path.join(path, 'builts')
    if uw.mpi.rank == 0:
        assert os.path.isdir(builtsDir)
    outDict = {}
    for name in sorted(names):
        outDict[name] = []
        jsonName = name + 'inputs'
        inputDict = load_json(jsonName, builtsDir)
        maxIndex = len(inputDict) - 1
        index = 0
        while index <= maxIndex:
            scriptName = name + 'script_' + str(index) + '.py'
            scriptPath = os.path.join(
                path,
                scriptName
                )
            fileCheck = False
            if uw.mpi.rank == 0:
                fileCheck = os.path.isfile(scriptPath)
            fileCheck = uw.mpi.comm.bcast(fileCheck, root = 0)
            assert fileCheck
            scriptModule = utilities.local_import(
                scriptPath
                )
            builtInputsName = jsonName + '_' + str(index)
            builtInputs = inputDict[builtInputsName]
            builtObj = scriptModule.build(**builtInputs)
            outDict[name].append(builtObj)
            index += 1
    return outDict

def get_inputs(builts):
    outDict = {}
    for name, builts in sorted(builts.items()):
        inputsName = name + 'inputs'
        outDict[inputsName] = []
        for index, built in enumerate(builts):
            subInputsName = inputsName + '_' + str(index)
            outDict[inputsName].append(built.inputs)


def find_checkpoints(path, stamps):
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
    return checkpoints_found

class Frame:

    _required_attributes = {
        'outputPath', # must be str
        'instanceID', # must be str
        '_is_child', # must be bool
        'inFrames', # must be list of Frames objects
        '_autoarchive', # must be bool
        'stamps', # must be dict
        'step', # must be int
        'stamps', # dict
        'saveVars', # dict of vars
        'figs', # figs to save
        'collectors',
        'scripts',
        'inputs',
        'subCheckpointFns',
        'update',
        'initialise',
        }

    def __init__(self):

        check_reqs(self)

        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarname = self.instanceID + '.tar.gz'
        self.tarpath = os.path.join(self.outputPath, self.tarname)
        self.backupdir = os.path.join(self.outputPath, 'backup')
        self.backuppath = os.path.join(self.backupdir, self.instanceID)
        self.backuptarpath = os.path.join(self.backupdir, self.tarname)

        self.archived = False #_isArchived

        self.blackhole = [0., 0.]

        self.checkpoints = []

        self.checkpointer = checkpoint.Checkpointer(
            step = self.step,
            modeltime = self.modeltime,
            saveVars = self.saveVars,
            figs = self.figs,
            dataCollectors = self.collectors,
            scripts = self.scripts,
            inputs = self.inputs,
            stamps = self.stamps,
            inFrames = self.inFrames,
            )

        self.initialise()

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
            for subCheckpointFn in self.subCheckpointFns:
                subCheckpointFn()
            # for observerName, observer \
            #         in sorted(self.observers.items()):
            #     observer.checkpoint(path)

            if self._autoarchive:
                self.archive()

            if self._autobackup:
                self.backup()

        else:

            self.checkpointer.checkpoint(path)

            # no need to checkpoint observers for remote

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
            self.status = "ready"

            if self._autoarchive and not self._is_child:
                self.archive()

            message("Checkpoint successfully loaded!")

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

        self.checkpoints = find_checkpoints(self.path, self.stamps)

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
