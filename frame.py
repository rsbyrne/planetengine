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
        autoarchive = True
        ):
    '''
    Creates a new 'frame' instance attached to a pre-existing
    model directory. LoadStep can be an integer corresponding
    to a previous checkpoint step, or can be the string 'max'
    which loads the highest stable checkpoint available.
    '''

    path = os.path.join(outputPath, instanceID)
    tarpath = path + '.tar.gz'

    if os.path.isfile(tarpath):
        if rank == 0:
            if not os.path.isdir(path):
                print("Tar found - unarchiving...")
                with tarfile.open(tarpath) as tar:
                    tar.extractall()
                print("Unarchived.")
                if not os.path.isdir(path):
                    raise Exception("Archive contained the wrong model file somehow.")
            else:
                raise Exception("Conflicting archive and directory found.")

    with open(os.path.join(path, 'inputs.txt')) as json_file:  
        inputs = json.load(json_file)
    params = inputs['params']
    options = inputs['options']
    config = inputs['config']

    systemscript = utilities.local_import(os.path.join(path, '_systemscript.py'))
    system = systemscript.build(**inputs['params'])

    initial = {}
    for varName in sorted(system.varsOfState):
        initialLoadName = '_' + varName + '_initial.py'
        module = utilities.local_import(
            os.path.join(path, initialLoadName)
            )
        # check if an identical 'initial' object already exists:
        if module.IC in [type(IC) for IC in initial.values()]:
            for priorVarName, IC in sorted(initial.items()):
                if type(IC) == module.IC and config[varName] == config[priorVarName]:
                    initial[varName] = initial[priorVarName]
                    break
        elif hasattr(module, 'LOADTYPE'):
            initial[varName] = module.IC(**config[varName], _outputPath = path)
        else:
            initial[varName] = module.IC(**config[varName])

    observerscript = utilities.local_import(os.path.join(path, '_observerscript.py'))
    observer = observerscript.build(**inputs['options'])

    with open(os.path.join(path, 'stamps.txt')) as json_file:
        stamps = json.load(json_file)

    frame = Frame(
        system = system,
        observer = observer,
        initial = initial,
        outputPath = outputPath,
        instanceID = instanceID,
        autoarchive = autoarchive,
        _stamps = stamps
        )

    checkpoints = []
    for directory in glob(path + '/*/'):
        basename = os.path.basename(directory[:-1])
        if (basename.isdigit() and len(basename) == 8):
            if os.path.exists(directory + 'stamps.txt'):
                checkpoints.append(int(basename))
    frame.checkpoints = sorted(checkpoints)

    if loadStep == 'max':
        frame.load_checkpoint(frame.checkpoints[-1])
    elif loadStep > 0:
        frame.load_checkpoint(loadStep)
    elif loadStep == 0:
        pass
    else:
        raise Exception("LoadStep input not understood.")

    return frame

class Frame:

    def __init__(self,
            system,
            observer,
            initial,
            outputPath = '',
            instanceID = None,
            autoarchive = True,
            _stamps = None,
            _use_wordhash = True,
            ):
        '''
        'system' should be the object produced by the 'build' call
        of a legitimate 'systemscript'.
        'observer'... ?
        'initial' should be a dictionary with an entry for each var mentioned
        in the system 'varsOfState' attribute, indexed by var name, e.g.:
        initial = {'temperatureField': tempIC, 'materialVar': materialIC}
        ...where 'tempIC' and 'materialIC' are instances of legitimate
        initial condition classes.
        '''

        self.outputPath = outputPath

        assert system.varsOfState.keys() == initial.keys()

        if _stamps == None:
            self.stamps = {
                'params': utilities.dictstamp(system.inputs),
                'options': utilities.dictstamp(observer.inputs),
                'system': utilities.scriptstamp(system.script),
                'observer': utilities.scriptstamp(observer.script),
                'config': utilities.dictstamp({
                    'scripts': utilities.multiscriptstamp(
                        [IC.script for name, IC in sorted(initial.items())]
                        ),
                    'inputs': utilities.multidictstamp(
                        [IC.inputs for name, IC in sorted(initial.items())]
                        ),
                    }),
                }
            self.allstamp = utilities.dictstamp(self.stamps)
            self.stamps['allstamp'] = self.allstamp
        else:
            self.stamps = _stamps

        for key in self.stamps:
            setattr(self, key, self.stamps[key])

        self._use_wordhash = _use_wordhash
        self.wordhash = planetengine.wordhash.wordhash(self.allstamp)
        if self._use_wordhash:
            self.hashID = 'pemod_' + self.wordhash
        else:
            self.hashID = 'pemod_' + self.allstamp
        if instanceID == None:
            self.instanceID = self.hashID
        else:
            self.instanceID = instanceID

        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarpath = self.path + '.tar.gz'
        self.autoarchive = autoarchive

        assert not (os.path.isdir(self.path) and os.path.isfile(self.tarpath)), \
            "Model directory and model archive cannot share same directory!"

        if os.path.isfile(self.tarpath):
            self.archived = True
        else:
            self.archived = False
                          
        self.system = system
        self.initial = initial
        self.observer = observer
        self.tools = observer.make_tools(self.system)
        self.figs = observer.make_figs(self.system, self.tools)
        self.data = observer.make_data(self.system, self.tools)

        self.varsOfState = self.system.varsOfState

        self.scripts = dict(
            {'systemscript': system.script, 'observerscript': observer.script},
            **{name + '_initial': IC.script for name, IC in self.initial.items()}
            )

        self.params = self.system.inputs
        self.options = self.observer.inputs
        self.config = {varName: IC.inputs for varName, IC in sorted(self.initial.items())}
        self.inputs = {
            'params': self.params,
            'options': self.options,
            'config': self.config,
            }

        self.inFrames = {}
        for IC in self.initial.values():
            if type(IC) == planetengine.initials.load.IC:
                self.inFrames[IC.inFrame.hashID] = IC.inFrame

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.system.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data['collectors'],
            scripts = self.scripts,
            inputs = self.inputs,
            stamps = self.stamps,
            path = self.path,
#             outputPath = self.outputPath,
#             instanceID = self.instanceID,
#             archive = archive,
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

    def initialise(self):
        if rank == 0:
            print("Initialising...")
        planetengine.initials.apply(self.initial, self.system)
        self.solved = False
        self.most_recent_checkpoint = None
        self.update()
        self.status = "ready"
        if rank == 0:
            print("Initialisation complete!")

    def reset(self):
        self.initialise()

    def checkpoint(self):
        if not self.allCollected:
            self.all_collect()

        if self.archived:
            self.unarchive()

        self.checkpointer.checkpoint()
        if self.autoarchive:
            self.archive()

        self.most_recent_checkpoint = self.step
        self.checkpoints.append(self.step)

    def update(self):
        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value
        self.allAnalysed = False
        self.allCollected = False
        self.allProjected = False

    def all_analyse(self):
        if rank == 0:
            print("Analysing...")
        if not self.solved:
            self.system.solve()
            self.solved = True
        if not self.allProjected:
            self.project()
            self.allProjected = True
        for analyser in self.data['analysers']:
            analyser.analyse()
        self.allAnalysed = True
        if rank == 0:
            print("Analysis complete!")

    def report(self):
        if rank == 0:
            print("Reporting...")
#         utilities.quickShow(*sorted(self.system.varsOfState.values()))
        if not self.allAnalysed:
            self.all_analyse()
        for analyser in self.data['analysers']:
            analyser.report()
        for figname in self.figs:
            if rank == 0:
                print(figname)
            self.figs[figname].show()
        if rank == 0:
            print("Reporting complete!")

    def all_collect(self):
        if rank == 0:
            print("Collecting...")
        if not self.allAnalysed:
            self.all_analyse()
        for collector in self.data['collectors']:
            collector.collect()
        self.allCollected = True
        if rank == 0:
            print("Collecting complete!")

    def all_clear(self):
        for collector in self.data['collectors']:
            collector.clear()

    def iterate(self):
        if rank == 0:
            print("Iterating step " + str(self.step) + " ...")
        self.system.iterate()
        self.update()
        self.solved = True
        if rank == 0:
            print("Iteration complete!")

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

        if rank == 0:
            print("Running...")

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
                    if rank == 0:
                        print("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        self.status = "post-traverse"
        if rank == 0:
            print("Done!")
        if checkpointCondition():
            self.checkpoint()
        self.status = "ready"

    def archive(self, prefix = ''):

        planetengine.message("Archiving...")

        assert os.path.isdir(self.path), \
            "Nothing to archive yet!"
        assert not os.path.isfile(self.tarpath), \
            "Destination archive already exists!"

        if rank == 0:
            with tarfile.open(self.tarpath, 'w:gz') as tar:
                tar.add(self.path)

        assert os.path.isfile(self.tarpath), \
            "The archive should have saved, but we can't find it!"

        planetengine.message("Deleting model directory...")

        if rank == 0:
            shutil.rmtree(self.path)

        planetengine.message("Model directory deleted.")

        self.archived = True

        planetengine.message("Archived!")

    def unarchive(self, prefix = ''):

        planetengine.message("Unarchiving...")

        assert not os.path.isdir(self.path), \
            "Destination directory already exists!"
        assert os.path.isfile(self.tarpath), \
            "No archive to unpack!"

        if rank == 0:
            with tarfile.open(self.tarpath) as tar:
                tar.extractall()

        assert os.path.isdir(self.path), \
            "The model directory doesn't appear to exist."

        planetengine.message("Deleting archive...")

        if rank == 0:
            os.remove(self.tarpath)

        planetengine.message("Model directory deleted.")

        self.archived = False

        planetengine.message("Unarchived!")

    def load_checkpoint(self, loadStep):

        if rank == 0:
            print("Loading checkpoint...")

        if loadStep == self.step:
            if rank == 0:
                print("Already at step ", str(loadStep), " - aborting load_checkpoint.")

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

            snapshot = os.path.join(checkpointFile, 'zerodData_snapshot.txt')
            with open(snapshot, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                header, data = csv_reader
            dataDict = {}
            for dataName, dataItem in zip(header, data):
                key = dataName[1:].lstrip()
                dataDict[key] = dataItem

            self.system.step.value = loadStep
            self.system.modeltime.value = float(dataDict['modeltime'])

            self.system.solve()

            self.update()
            self.status = "ready"

            if self.autoarchive:
                self.archive()

            if rank == 0:
                print("Checkpoint successfully loaded!")
