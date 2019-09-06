import numpy as np
import underworld as uw
from underworld import function as fn
import math
import time
import tarfile
import os
import shutil
import json
import itertools
import inspect
import importlib
import csv
import copy
from glob import glob

from . import utilities
from .wordhash import wordhash as wordhashFn
from . import checkpoint
from .initials.load import IC as _loadIC
from .initials import apply
from .utilities import message
from .visualisation import QuickFig

def expose_tar(path):

    tarpath = path + '.tar.gz'

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

def load_inputs(inputName, path):
    filename = inputName + '.json'
    inputDict = {}
    if uw.mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            inputDict = json.load(json_file)
    inputDict = uw.mpi.comm.bcast(inputDict, root = 0)
    return inputDict

def load_system(path):
    params = load_inputs('params', path)
    systemscript = utilities.local_import(os.path.join(path, 'systemscript_0.py'))
    system = systemscript.build(**params)
    return system, params

def load_initials(system, path):
    configs = load_inputs('configs', path)
    initials = {}
    for varName in sorted(system.varsOfState):
        initials[varName] = {**configs[varName]}
        initialsLoadName = varName + '_initialscript_0.py'
        module = utilities.local_import(
            os.path.join(path, initialsLoadName)
            )
        # check if an identical 'initial' object already exists:
        if hasattr(module, 'LOADTYPE'):
            initials[varName] = _loadIC(
                **configs[varName], _outputPath = path, _is_child = True
                )
        elif module.IC in [type(IC) for IC in initials.values()]:
            for priorVarName, IC in sorted(initials.items()):
                if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
                    initials[varName] = initials[priorVarName]
                    break
        else:
            initials[varName] = module.IC(
                **configs[varName]
                )
    return initials, configs

# def load_observers(system, initials, path):
#     options = load_inputs('options', path)
#     observers = []


def find_checkpoints(path, stamps):
    checkpoints_found = []
    if uw.mpi.rank == 0:
        for directory in glob(path + '/*/'):
            basename = os.path.basename(directory[:-1])
            if (basename.isdigit() and len(basename) == 8):
                with open(os.path.join(directory, 'stamps.json')) as json_file:
                    loadstamps = json.load(json_file)
#                 with open(os.path.join(path, 'inputs.txt')) as json_file:
#                     loadconfig = json.load(json_file)
                assert loadstamps == stamps, \
                    "Bad checkpoint found! Aborting."
                message("Found checkpoint: " + basename)
                checkpoints_found.append(int(basename))
        checkpoints_found = sorted(list(set(checkpoints_found)))
    checkpoints_found = uw.mpi.comm.bcast(checkpoints_found, root = 0)
    return checkpoints_found

def load_frame(
        outputPath = '',
        instanceID = '',
        loadStep = 0,
        _is_child = False,
        ):
    '''
    Creates a new 'frame' instance attached to a pre-existing
    model directory. LoadStep can be an integer corresponding
    to a previous checkpoint step, or can be the string 'max'
    which loads the highest stable checkpoint available.
    '''

    # Check that target directory is not inside
    # another planetengine directory:

    if not _is_child:
        if uw.mpi.rank == 0:
            assert not os.path.isfile(os.path.join(outputPath, 'stamps.json')), \
                "Loading a child model as an independent frame \
                not currently supported."

    path = os.path.join(outputPath, instanceID)

    expose_tar(path)

    system, params = load_system(path)

    initials, configs = load_initials(system, path)

    # observers, options = load_observers(system, initials, path)

    frame = Frame(
        system = system,
#         observers = observers,
        initials = initials,
        outputPath = outputPath,
        instanceID = instanceID,
        _is_child = _is_child
        )

    # we may know it's a child already,
    # but we may not have constructed the parent yet.

    # If it's a loaded frame, it must have been saved to disk at some point -
    # hence its internal frames will all be held as copies inside
    # the loaded frame. We need to flag this:
    for inFrame in frame.inFrames:
        inFrame._parentFrame = frame

    frame.checkpoints = find_checkpoints(path, frame.stamps)

    frame.load_checkpoint(loadStep)

    frame.onDisk = True # since you just loaded from disk!

    if all([
            frame._autoarchive,
            not frame.archived,
            not _is_child
            ]):
        frame.archive()

    return frame

def _make_stamps(
        params,
        systemscripts,
        # options,
        # observerscripts,
        configs,
        initialscripts
        ):

    message("Making stamps...")

    stamps = {}
    if uw.mpi.rank == 0:
        stamps = {
            'params': utilities.hashstamp(params),
            'systemscripts': utilities.hashstamp(
                [open(script) for script in systemscripts]
                ),
            # 'options': utilities.hashstamp(options),
            # 'observerscripts': utilities.hashstamp(
            #     [open(script) for script in observerscripts]
            #     ),
            'configs': utilities.hashstamp(configs),
            'initialscripts': utilities.hashstamp(
                [open(script) for script in initialscripts]
                )
            }
        stamps['allstamp'] = utilities.hashstamp(
            [val for key, val in sorted(stamps.items())]
            )
        stamps['system'] = utilities.hashstamp(
            (stamps['params'], stamps['systemscripts'])
            )
        # stamps['observers'] = utilities.hashstamp(
        #     (stamps['options'], stamps['observers'])
        #     )
        stamps['initials'] = utilities.hashstamp(
            (stamps['configs'], stamps['initialscripts'])
            )
        for stampKey, stampVal in stamps.items():
            stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
    stamps = uw.mpi.comm.bcast(stamps, root = 0)

    message("Stamps made.")

    return stamps

def _scripts_and_stamps(
        system,
        initials,
        # observers
        ):

    scripts = {}

    systemscripts = []
    for index, script in enumerate(system.scripts):
        scriptname = 'systemscript' + '_' + str(index)
        scripts[scriptname] = script
        systemscripts.append(script)
    params = system.inputs

    configs = {}
    initialscripts = []
    for varName, IC in sorted(initials.items()):
        for index, script in enumerate(IC.scripts):
            scriptname = varName + '_initialscript_' + str(index)
            scripts[scriptname] = script
            initialscripts.append(script)
        configs[varName] = IC.inputs

    # options = {}
    # observerscripts = []
    # for observer in observers:
    #     observerName = observer.hashID
    #     for index, script in enumerate(observer.scripts):
    #         scriptname = observerName + '_observerscript_' + str(index)
    #         scripts[scriptname] = script
    #         observerscripts.append(script)
    #     options[observerName] = observer.inputs

    stamps = _make_stamps(
        params,
        systemscripts,
        # options,
        # observerscripts,
        configs,
        initialscripts
        )

    inputs = {
        'params': params,
        # 'options': options,
        'configs': configs,
        }

    return inputs, stamps, scripts

################

class _Frame:

    _required_attributes = {
        'system', # must be a 'system'-like object
        'initials', # must be dict (key = str, val = IC)
        'outputPath', # must be str
        'instanceID', # must be str
        '_is_child', # must be bool
        'inFrames', # must be list of Frames objects
        '_autoarchive', # must be bool
        'checkpoint', # must take pos arg (path)
        'load_checkpoint', # must take pos arg (step)
        'stamps', # must be dict
        'step', # must be int
        }

    def __init__(self):

        for attrname in self._required_attributes:
            if not hasattr(self, attrname):
                raise Exception(
                    "Self requires attribute: '" + attrname + "'"
                    )

        assert self.system.varsOfState.keys() == self.initials.keys()

        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarname = self.instanceID + '.tar.gz'
        self.tarpath = os.path.join(self.outputPath, self.tarname)
        self.backupdir = os.path.join(self.outputPath, 'backup')
        self.backuppath = os.path.join(self.backupdir, self.instanceID)
        self.backuptarpath = os.path.join(self.backupdir, self.tarname)

        self.archived = False #_isArchived
        self.onDisk = False

        if type(self.system.mesh) == uw.mesh._spherical_mesh.FeMesh_Annulus:
            self.blackhole = [0., 0.]
        else:
            raise Exception("Only the Annulus mesh is supported at this time.")

        self.checkpoints = []

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

        if not self.onDisk and (_path is None or _path == self.path):
            message("Nothing to archive yet!")
            return None
        if self.archived and (_path is None or _path == self.path):
            message("Already archived!")
            return None
        if self._is_child:
            message("Bumping archive call up to parent...")
            self._parentFrame.archive(_path)

        else:

            message("Archiving...")

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

            if uw.mpi.rank == 0:

                print(path)
                assert os.path.isdir(path), \
                    "Nothing to archive yet!"
                assert not os.path.isfile(tarpath), \
                    "Destination archive already exists!"

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

        if not self.onDisk and (_path is None or _path == self.path):
            message("Nothing to unarchive yet!")
            return None
        if not self.archived and (_path is None or _path == self.path):
            message("Already unarchived!")
            return None
        if self._is_child:
            message("Bumping unarchive call up to parent...")
            self._parentFrame.unarchive(_path)

        else:

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

def make_frame(
        system,
        initials,
        outputPath = '',
        instanceID = None,
        ):

    inputs, stamps, scripts = \
        _scripts_and_stamps(system, initials)
    params = inputs['params']
    # options = inputs['options']
    configs = inputs['configs']

    if instanceID is None:
        instanceID = 'pemod_' + stamps['allstamp'][1]

    path = os.path.join(outputPath, instanceID)
    tarpath = path + '.tar.gz'

    directory_state = ''

    if uw.mpi.rank == 0:

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

    directory_state = uw.mpi.comm.bcast(directory_state, root = 0)

    if directory_state == 'tar':
        if uw.mpi.rank == 0:
            with tarfile.open(tarpath) as tar:
                tar.extract('stamps.json', path)
            with open(os.path.join(path, 'stamps.json')) as json_file:
                loadstamps = json.load(json_file)
            shutil.rmtree(path)
            assert loadstamps == stamps

    if directory_state == 'clean':
        message("Making a new frame...")
        frame = Frame(
            system,
            initials,
            outputPath,
            instanceID
            )

    else:
        message("Preexisting frame found! Loading...")
        frame = load_frame(
            outputPath,
            instanceID
            )

    return frame

class Frame(_Frame):

    def __init__(self,
            system,
            initials,
            outputPath = '',
            instanceID = 'test',
            _autoarchive = True,
            _parentFrame = None,
            _is_child = False,
            _autobackup = True,
            ):

        message("Building frame...")

        self.system = system
        self.observers = {}
        self.initials = initials
        self.outputPath = outputPath
        self.instanceID = instanceID
        self._autoarchive = _autoarchive
        self._parentFrame = _parentFrame
        self._is_child = _is_child
        self._autobackup = _autobackup

        inputs, stamps, scripts = \
            _scripts_and_stamps(system, initials)

        self.inputs = inputs
        self.params = inputs['params']
        # self.options = inputs['options']
        self.configs = inputs['configs']
        self.stamps = stamps
        self.scripts = scripts

        self.hashID = 'pemod_' + self.stamps['allstamp'][1]

        self.varsOfState = self.system.varsOfState
        self.step = 0
        self.modeltime = 0.

        self.inFrames = []
        for IC in self.initials.values():
            try:
                self.inFrames.append(IC.inFrame)
            except:
                pass

        self.analysers = []
        self.collectors = []
        self.fig = QuickFig(
            system.varsOfState,
            style = 'smallblack',
            )
        self.figs = [self.fig]

        self.checkpointer = checkpoint.Checkpointer(
            step = self.system.step,
            modeltime = self.system.modeltime,
            varsOfState = self.varsOfState,
            figs = self.figs,
            dataCollectors = self.collectors,
            scripts = self.scripts,
            inputs = self.inputs,
            stamps = self.stamps,
            inFrames = self.inFrames,
            )

        self.initialise()

        message("Frame built!")

        super().__init__()

    def initialise(self):
        message("Initialising...")
        apply(
            self.initials,
            self.system,
            )
        self.system.solve()
        self.most_recent_checkpoint = None
        self.update()
        self.status = "ready"
        message("Initialisation complete!")

    def reset(self):
        self.initialise()

    def all_analyse(self):
        message("Analysing...")
        for analyser in self.analysers:
            analyser.analyse()
        message("Analysis complete!")

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

    def update(self):
        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value
        for observerName, observer \
                in sorted(self.observers.items()):
            observer.prompt()

    def report(self):
        message(
            '\n' \
            + 'Step: ' + str(self.step) \
            + ', modeltime: ' + '%.3g' % self.modeltime
            )
        self.fig.show()

    def iterate(self):
        assert not self._is_child, \
            "Cannot iterate child models independently."
        message("Iterating step " + str(self.step) + " ...")
        self.system.iterate()
        self.update()
        message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step + steps
        self.traverse(lambda: self.step >= stopStep)

    def traverse(self, stopCondition,
            collectConditions = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            forge_on = False,
            ):

        self.status = "pre-traverse"

        if not type(collectConditions) is list:
            collectConditions = [collectConditions,]
            assert len(collectConditions) == len(self.collectors)

        if checkpointCondition():
            self.checkpoint()

        message("Running...")

        while not stopCondition():

            try:
                self.status = "traversing"
                self.iterate()
                if checkpointCondition():
                    self.checkpoint()
                else:
                    for collector, collectCondition in zip(
                            self.collectors,
                            collectConditions
                            ):
                        if collectCondition():
                            collector.collect()
                if reportCondition():
                    self.report()

            except:
                if forge_on:
                    message("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        self.status = "post-traverse"
        message("Done!")
        if checkpointCondition():
            self.checkpoint()
        self.status = "ready"

    def checkpoint(self, path = None):

        if self.archived:
            self.unarchive()

        self.all_collect()

        if path is None or path == self.path:

            path = self.path

            if self.step in self.checkpoints:
                message("Checkpoint already exists! Skipping.")
            else:
                self.checkpointer.checkpoint(path)

            self.all_clear()

            self.most_recent_checkpoint = self.step
            self.checkpoints.append(self.step)
            self.checkpoints = sorted(set(self.checkpoints))

            self.onDisk = True

            # CHECKPOINT OBSERVERS!!!
            for observerName, observer \
                    in sorted(self.observers.items()):
                observer.checkpoint(path)

        else:

            self.checkpointer.checkpoint(path)

            # no need to checkpoint observers for remote

        if self._autoarchive:
            self.archive()

        if self._autobackup:
            self.backup()

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

            utilities.varsOnDisk(
                self.system.varsOfState,
                checkpointFile,
                'load',
                self.blackhole
                )

            dataDict = {}
            if uw.mpi.rank == 0:
                filelist = sorted(os.listdir(checkpointFile))
                for file in filelist:
                    if '_snapshot.txt' in file:
                        # Any saved data will do:
                        snapshot = os.path.join(checkpointFile, file)
                        break
                with open(snapshot, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    header, data = csv_reader
                for dataName, dataItem in zip(header, data):
                    key = dataName[1:].lstrip()
                    dataDict[key] = dataItem
            dataDict = uw.mpi.comm.bcast({**dataDict}, root = 0)

            self.system.step.value = loadStep

            modeltime = 0.
            if uw.mpi.rank == 0:
                modeltime_filepath = os.path.join(
                    checkpointFile,
                    'modeltime.json'
                    )
                with open(modeltime_filepath, 'r') as file:
                    modeltime = json.load(file)
            modeltime = uw.mpi.comm.bcast(modeltime, root = 0)
            self.system.modeltime.value = modeltime

            self.system.solve()

            self.update()
            self.status = "ready"

            if self._autoarchive and not self._is_child:
                self.archive()

            message("Checkpoint successfully loaded!")

# An example of a custom class that inherits from _Frame:
class CustomFrame(_Frame):
    def __init__(self):

        system = planetengine.systems.arrhenius.build(res = 16)
        initials = {'temperatureField': planetengine.initials.sinusoidal.IC(freq = 1.)}
        planetengine.initials.apply(
            initials,
            system,
            )
        system.solve()

        self.system = system
        self.initials = initials
        self.outputPath = '/home/jovyan/workspace/data/test'
        self.instanceID = 'testFrame'
        self.stamps = {'a': 1}
        self.step = 0
        self.onDisk = False
        self._is_child = False
        self.inFrames = []
        self._autoarchive = True
        checkpointer = checkpoint.Checkpointer(
            stamps = self.stamps,
            step = system.step,
            modeltime = system.modeltime,
            )
        mypath = os.path.join(self.outputPath, self.instanceID)
        def checkpoint(path = None):
            if path is None:
                path = mypath
            checkpointer.checkpoint(path)
            self.onDisk = True
        self.checkpoint = checkpoint
        def load_checkpoint(step):
            pass
        self.load_checkpoint = load_checkpoint

        super().__init__()
