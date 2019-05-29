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

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

import planetengine
from planetengine import utilities

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
        if rank == 0:
            assert not os.path.isfile(os.path.join(outputPath, 'stamps.txt')), \
                "Loading a child model as an independent frame \
                not currently supported."

    path = os.path.join(outputPath, instanceID)
    tarpath = path + '.tar.gz'

    if rank == 0:
        assert os.path.isdir(path) or os.path.isfile(tarpath), \
            "No model found at that directory!"

    if rank == 0:
        if os.path.isfile(tarpath):
            assert not os.path.isdir(path), \
                "Conflicting archive and directory found."
            planetengine.message("Tar found - unarchiving...")
            with tarfile.open(tarpath) as tar:
                tar.extractall(path)
            planetengine.message("Unarchived.")
            assert os.path.isdir(path), \
                "Archive contained the wrong model file somehow."
            os.remove(tarpath)

    inputs = {}
    if rank == 0:
        with open(os.path.join(path, 'inputs.txt')) as json_file:  
            inputs = json.load(json_file)
    inputs = comm.bcast(inputs, root = 0)

    params = inputs['params']
    options = inputs['options']
    configs = inputs['configs']

    systemscript = utilities.local_import(os.path.join(path, '_systemscript.py'))
    system = systemscript.build(**inputs['params'])

    initials = {}
    for varName in sorted(system.varsOfState):
        initials[varName] = {**configs[varName]}
        initialsLoadName = '_' + varName + '_initials.py'
        module = utilities.local_import(
            os.path.join(path, initialsLoadName)
            )
        # check if an identical 'initial' object already exists:
        if module.IC in [type(IC) for IC in initials.values()]:
            for priorVarName, IC in sorted(initials.items()):
                if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
                    initials[varName] = initials[priorVarName]
                    break
        elif hasattr(module, 'LOADTYPE'):
            initials[varName] = module.IC(
                **configs[varName], _outputPath = path, _is_child = True
                )
        else:
            initials[varName] = module.IC(
                **configs[varName]
                )

    observerscript = utilities.local_import(
        os.path.join(path, '_observerscript.py')
        )
    observer = observerscript.build(**inputs['options'])

    frame = Frame(
        system = system,
        observer = observer,
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

    if rank == 0:
        for directory in glob(path + '/*/'):
            basename = os.path.basename(directory[:-1])
            if (basename.isdigit() and len(basename) == 8):
                with open(os.path.join(directory, 'stamps.txt')) as json_file:
                    loadstamps = json.load(json_file)
                with open(os.path.join(path, 'inputs.txt')) as json_file:
                    loadconfig = json.load(json_file)
                assert loadstamps == frame.stamps, \
                    "Bad checkpoint found! Aborting."
                planetengine.message("Found checkpoint: " + basename)
                frame.checkpoints.append(int(basename))
        frame.checkpoints = sorted(list(set(frame.checkpoints)))
    frame.checkpoints = comm.bcast(frame.checkpoints, root = 0)

    if loadStep == 'max':
        frame.load_checkpoint(frame.checkpoints[-1])
    elif loadStep > 0:
        frame.load_checkpoint(loadStep)
    elif loadStep == 0:
        pass
    else:
        raise Exception("LoadStep input not understood.")

    if all([frame.autoarchive, not frame.archived, not _is_child]):
        frame.archive()

    return frame

def make_stamps(
        params,
        options,
        configs,
        scripts,
        _use_wordhash = True,
        ):

    planetengine.message("Making stamps...")

    stamps = {}
    if rank == 0:
        openScripts = {
            name: open(script) \
            for name, script in sorted(scripts.items())
            }

        stamps = {
            'params': utilities.hashstamp(params),
            'options': utilities.hashstamp(options),
            'configs': utilities.hashstamp(configs),
            'scripts': utilities.hashstamp(openScripts)
            }
        stamps['allstamp'] = utilities.hashstamp(stamps)

    stamps = comm.bcast(stamps, root = 0)

    wordhash = planetengine.wordhash.wordhash(stamps['allstamp'])
    if _use_wordhash:
        hashID = 'pemod_' + wordhash
    else:
        hashID = 'pemod_' + stamps['allstamp']

    planetengine.message("Stamps made.")

    return stamps, hashID

def make_frame(
        system,
        observer,
        initials,
        outputPath = '',
        instanceID = None,
        ):
    '''
    'system' should be the object produced by the 'build' call
    of a legitimate 'systemscript'.
    'observer'... ?
    'initials' should be a dictionary with an entry for each var mentioned
    in the system 'varsOfState' attribute, indexed by var name, e.g.:
    initials = {'temperatureField': tempIC, 'materialVar': materialIC}
    ...where 'tempIC' and 'materialIC' are instances of legitimate
    initials condition classes.
    '''

    planetengine.message("Making a new frame...")

    scripts = {
        'systemscript': system.script,
        'observerscript': observer.script
        }

    configs = {}
    for varName, IC in sorted(initials.items()):
        scripts[varName + '_initials'] = IC.script
        configs[varName] = IC.inputs

    stamps, hashID = make_stamps(
        system.inputs,
        observer.inputs,
        configs,
        scripts
        )

    if instanceID == None:
        instanceID = hashID

    path = os.path.join(outputPath, instanceID)
    tarpath = path + '.tar.gz'

    directory_state = ''

    if rank == 0:

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

    directory_state = comm.bcast(directory_state, root = 0)

    if directory_state == 'tar':
        if rank == 0:
            with tarfile.open(tarpath) as tar:
                tar.extract('stamps.txt', path)
            with open(os.path.join(path, 'stamps.txt')) as json_file:
                loadstamps = json.load(json_file)
            os.remove(os.path.join(path, 'stamps.txt'))
            assert loadstamps == stamps

    if directory_state == 'clean':
        frame = Frame(
            system,
            observer,
            initials,
            outputPath,
            instanceID
            )

    else:
        frame = load_frame(
            outputPath,
            instanceID
            )

    planetengine.message("Frame made.")

    return frame

################

class Frame:

    def __init__(self,
            system,
            observer,
            initials,
            outputPath = '',
            instanceID = 'test',
            autoarchive = True,
            _parentFrame = None,
            _is_child = False
            ):
        '''
        'system' should be the object produced by the 'build' call
        of a legitimate 'systemscript'.
        'observer'... ?
        'initials' should be a dictionary with an entry for each var mentioned
        in the system 'varsOfState' attribute, indexed by var name, e.g.:
        initials = {'temperatureField': tempIC, 'materialVar': materialIC}
        ...where 'tempIC' and 'materialIC' are instances of legitimate
        initials condition classes.
        '''

        assert system.varsOfState.keys() == initials.keys()

        planetengine.message("Building frame...")

        self.system = system
        self.observer = observer
        self.initials = initials
        self.outputPath = outputPath
        self.instanceID = instanceID
        self.autoarchive = autoarchive
        self._parentFrame = _parentFrame
        self._is_child = _is_child

        scripts = {
            'systemscript': system.script,
            'observerscript': observer.script
            }

        configs = {}
        for varName, IC in sorted(initials.items()):
            scripts[varName + '_initials'] = IC.script
            configs[varName] = IC.inputs

        self.params = self.system.inputs
        self.options = self.observer.inputs
        self.configs = configs
        self.scripts = scripts

        self.inputs = {
            'params': self.params,
            'options': self.options,
            'configs': self.configs
            }

        self.stamps, self.hashID = make_stamps(
            self.params,
            self.options,
            self.configs,
            self.scripts
            )

        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarname = self.instanceID + '.tar.gz'
        self.tarpath = os.path.join(self.outputPath, self.tarname)

        self.archived = False #_isArchived
        self.checkpoints = []

        planetengine.message("Doing stuff with the observer...")

        self.tools = observer.make_tools(self.system)
        self.figs = observer.make_figs(self.system, self.tools)
        self.data = observer.make_data(self.system, self.tools)

        planetengine.message("Observer stuff complete.")

        self.varsOfState = self.system.varsOfState

#         if varsOfState is None:
#             try: self.varsOfState = self.system.varsOfState
#             except: raise Exception("No vars of state provided!")
#         else:
#             self.varsOfState = varsOfState
#         if varScales is None:
#             try: self.varsOfState = self.system.varsOfState

        planetengine.message("Loading interior frames...")
        self.inFrames = []
        for IC in self.initials.values():
            try:
                self.inFrames.append(IC.inFrame)
            except:
                pass
        planetengine.message(
            "Loaded " + str(len(self.inFrames)) + " interior frames."
            )

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.system.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data['collectors'],
            scripts = self.scripts,
            inputs = self.inputs,
            stamps = self.stamps,
            inFrames = self.inFrames
            )

        self.observerDict = {}

        self.projections, self.projectors, self.project = utilities.make_projectors(
            {**self.system.varsOfState, **self.observerDict}
            )
        # CHANGED WHEN NEW FEATURES ARE READY:
        try:
            self.projections.update(self.tools.projections)
            self.projectors.update(self.tools.projectors)
        except:
            pass

        if type(self.system.mesh) == uw.mesh._spherical_mesh.FeMesh_Annulus:
            self.blackhole = [0., 0.]
        else:
            raise Exception("Only the Annulus mesh is supported at this time.")

        self.checkpoints = []

        self.initialise()

        planetengine.message("Frame built!")

    def initialise(self):
        planetengine.message("Initialising...")
        planetengine.initials.apply(
            self.initials, 
            self.system,
            )
        self.system.solve()
        self.most_recent_checkpoint = None
        self.update()
        self.status = "ready"
        planetengine.message("Initialisation complete!")

    def reset(self):
        self.initialise()

    def checkpoint(self, path = None, archive_remote = False):

        if self.archived:
            self.unarchive()

        if path is None or path == self.path:

            if not self.allCollected:
                self.all_collect()

            path = self.path

            if self.step in self.checkpoints:
                planetengine.message("Checkpoint already exists! Skipping.")
            else:
                self.checkpointer.checkpoint(path)

            self.most_recent_checkpoint = self.step
            self.checkpoints.append(self.step)

        else:

            self.all_analyse()

            self.checkpointer.checkpoint(path, clear_data = False)

            if archive_remote:
                self.archive(path)

        if self.autoarchive:
            self.archive()

    def update(self):
        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value
        self.allAnalysed = False
        self.allCollected = False
        self.allProjected = False

    def all_analyse(self):
        planetengine.message("Analysing...")
        if not self.allProjected:
            self.project()
            self.allProjected = True
        for analyser in self.data['analysers']:
            analyser.analyse()
        self.allAnalysed = True
        planetengine.message("Analysis complete!")

    def report(self):
        planetengine.message("Reporting...")
#         utilities.quickShow(*sorted(self.system.varsOfState.values()))
        if not self.allAnalysed:
            self.all_analyse()
        for analyser in self.data['analysers']:
            analyser.report()
        for figname in self.figs:
            if rank == 0:
                print(figname)
            self.figs[figname].show()
        planetengine.message("Reporting complete!")

    def all_collect(self):
        planetengine.message("Collecting...")
        if not self.allAnalysed:
            self.all_analyse()
        for collector in self.data['collectors']:
            collector.collect()
        self.allCollected = True
        planetengine.message("Collecting complete!")

    def all_clear(self):
        for collector in self.data['collectors']:
            collector.clear()

    def iterate(self):
        assert not self._is_child, \
            "Cannot iterate child models indendently."
        planetengine.message("Iterating step " + str(self.step) + " ...")
        self.system.iterate()
        self.update()
        planetengine.message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step + steps
        self.traverse(lambda: self.step >= stopStep)

    def traverse(self, stopCondition,
            collectCondition = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            forge_on = False,
            ):

        self.status = "pre-traverse"

        if checkpointCondition():
            self.checkpoint()

        planetengine.message("Running...")

        while not stopCondition():

            try:
                self.status = "traversing"
                self.iterate()
                if checkpointCondition():
                    self.checkpoint()
                elif collectCondition():
                    self.all_collect()
                if reportCondition():
                    self.report()

            except:
                if forge_on:
                    planetengine.message("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        self.status = "post-traverse"
        planetengine.message("Done!")
        if checkpointCondition():
            self.checkpoint()
        self.status = "ready"

    def fork(self, extPath, return_frame = False):

        planetengine.message("Forking model to new directory...")

        if rank == 0:

            if self.archived and not self._is_child:
                newpath = os.path.join(
                    extPath,
                    self.tarname
                    )
                shutil.copyfile(
                    self.tarpath,
                    newpath
                    )
                planetengine.message(
                    "Model forked to directory: " + extPath + self.tarname
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
                    planetengine.message(
                        "Model forked to directory: " + extPath + self.instanceID
                        )
                    if self.autoarchive:
                        self.archive()
                        self.archive(newpath)
                    hardFork = True
                else:
                    planetengine.message("No files to fork yet.")
                    hardFork = False

        if return_frame:
            if hardFork:
                planetengine.message(
                    "Loading newly forked frame at current model step: "
                    )
                newframe = load_frame(extPath, self.instanceID, loadStep = self.step)
                planetengine.message(
                    "Loaded newly forked frame."
                    )
            else:
                planetengine.message(
                    "Returning a copy of the current class object \
                    with a new outputPath."
                    )
                newframe = copy.deepcopy(self)
                newframe.outputPath = extPath

            return newframe

    def branch(self, extPath, return_frame = False, archive_remote = True):
        newpath = os.path.join(extPath, self.instanceID)
        self.checkpoint(
            newpath,
            archive_remote = archive_remote
            )
        if return_frame:
            newframe = load_frame(extPath, self.instanceID)
            return newframe

    def archive(self, _path = None):

        if self.archived and (_path is None or _path == self.path):
            planetengine.message("Already archived!")
            return None

        # If this frame happens to be located inside another frame,
        # we need to bump the call up to that parent frame:

        if self._is_child:
            planetengine.message("Bumping archive call up to parent...")
            self._parentFrame.archive(_path)

        else:

            planetengine.message("Archiving...")

            if _path is None or _path == self.path:
                path = self.path
                tarpath = self.tarpath
                localArchive = True
                planetengine.message("Making a local archive...")
            else:
                path = _path
                tarpath = path + '.tar.gz'
                localArchive = False
                planetengine.message("Making a remote archive...")

            if rank == 0:

                assert os.path.isdir(path), \
                    "Nothing to archive yet!"
                assert not os.path.isfile(tarpath), \
                    "Destination archive already exists!"

                with tarfile.open(tarpath, 'w:gz') as tar:
                    tar.add(path, arcname = '')

                assert os.path.isfile(tarpath), \
                    "The archive should have saved, but we can't find it!"

                planetengine.message("Deleting model directory...")

                shutil.rmtree(path)

                planetengine.message("Model directory deleted.")

            if localArchive:
                self._set_inner_archive_status(True)

            planetengine.message("Archived!")

    def unarchive(self, _path = None):

        if not self.archived and (_path is None or _path == self.path):
            planetengine.message("Already unarchived!")
            return None

        # If this frame happens to be located inside another frame,
        # we need to bump the call up to that parent frame:
        if self._is_child:
            planetengine.message("Bumping unarchive call up to parent...")
            self._parentFrame.unarchive(_path)

        else:

            planetengine.message("Unarchiving...")

            if _path is None or _path == self.path:
                path = self.path
                tarpath = self.tarpath
                localArchive = True
                planetengine.message("Unarchiving the local archive...")
            else:
                path = _path
                tarpath = path + '.tar.gz'
                localArchive = False
                planetengine.message("Unarchiving a remote archive...")

            if rank == 0:
                assert not os.path.isdir(path), \
                    "Destination directory already exists!"
                assert os.path.isfile(tarpath), \
                    "No archive to unpack!"

                with tarfile.open(tarpath) as tar:
                    tar.extractall(path)

                assert os.path.isdir(path), \
                    "The model directory doesn't appear to exist."

                planetengine.message("Deleting archive...")

                os.remove(tarpath)

                planetengine.message("Model directory deleted.")

            if localArchive:
                self._set_inner_archive_status(False)

            planetengine.message("Unarchived!")

    def _set_inner_archive_status(self, status):
        self.archived = status
        for inFrame in self.inFrames:
            if inFrame._is_child:
                inFrame._set_inner_archive_status(status)

    def load_checkpoint(self, loadStep):

        planetengine.message("Loading checkpoint...")

        if loadStep == 'max':
            loadStep = max(self.checkpoints)
        elif loadStep == 'min':
            loadStep = min(self.checkpoints)
        elif loadStep == 'latest':
            loadStep = self.most_recent_checkpoint

        if loadStep == self.step:
            planetengine.message(
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
            if rank == 0:
                snapshot = os.path.join(checkpointFile, 'zerodData_snapshot.txt')
                with open(snapshot, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    header, data = csv_reader
                for dataName, dataItem in zip(header, data):
                    key = dataName[1:].lstrip()
                    dataDict[key] = dataItem
            dataDict = comm.bcast({**dataDict}, root = 0)

            self.system.step.value = loadStep
            self.system.modeltime.value = float(dataDict['modeltime'])

            self.system.solve()

            self.update()
            self.status = "ready"

            if self.autoarchive and not self._is_child:
                self.archive()

            planetengine.message("Checkpoint successfully loaded!")
