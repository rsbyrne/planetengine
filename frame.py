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

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

import planetengine
from planetengine import utilities

def load_frame(outputPath = '', instanceID = '', loadStep = 0):

    loadpath = os.path.join(outputPath, instanceID)

    with open(os.path.join(loadpath, 'inputs.txt')) as json_file:  
        inputs = json.load(json_file)
    params = inputs['params']
    options = inputs['options']
    config = inputs['config']

    systemscript = utilities.local_import(os.path.join(loadpath, '_systemscript.py'))
    system = systemscript.build(**inputs['params'])

    initial = {}
    for varName in sorted(system.varsOfState):
        initialLoadName = '_' + varName + '_initial.py'
        module = utilities.local_import(
            os.path.join(loadpath, initialLoadName)
            )
        initial[varName] = module.IC(**config[varName])

    observerscript = utilities.local_import(os.path.join(loadpath, '_observerscript.py'))
    observer = observerscript.build(**inputs['options'])

    with open(os.path.join(loadpath, 'stamps.txt')) as json_file:
        stamps = json.load(json_file)

    frame = Frame(
        system = system,
        observer = observer,
        initial = initial,
        outputPath = outputPath,
        instanceID = instanceID,
        _stamps = stamps,
        )

    if loadStep > 0:
        frame.load_checkpoint(loadStep)

    return frame

class Frame:

    def __init__(self,
            system,
            observer,
            initial,
            outputPath = '',
            instanceID = None,
            archive = False,
            _stamps = None,
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

        if instanceID == None:
            self.instanceID = 'pemod_' + self.allstamp
        else:
            self.instanceID = instanceID

        self.path = os.path.join(outputPath, self.instanceID)

        self.system = system
        self.initial = initial
        self.observer = observer
        self.tools = observer.make_tools(self.system)
        self.figs = observer.make_figs(self.system, self.tools)
        self.data = observer.make_data(self.system, self.tools)

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

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.system.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data['collectors'],
            scripts = self.scripts,
            inputs = self.inputs,
            stamps = self.stamps,
            path = self.path,
            archive = archive,
            )

        self.reset()

    def checkpoint(self):
        if not self.allDataCollected:
            self.all_collect()
        self.checkpointer.checkpoint()
        self.most_recent_check = self.step

    def update(self):
        try:
            for projectorName, projector in sorted(self.tools.projectors.items()):
                projector.solve()
        except AttributeError:
            pass
        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value
        self.allDataRefreshed = False
        self.allDataCollected = False

    def all_analyse(self):
        for analyser in self.data['analysers']:
            analyser.analyse()
        self.allDataRefreshed = True

    def report(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for analyser in self.data['analysers']:
            analyser.report()
        for figname in self.figs:
            if rank == 0:
                print(figname)
            self.figs[figname].show()

    def all_collect(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for collector in self.data['collectors']:
            collector.collect()
        self.allDataCollected = True

    def all_clear(self):
        for collector in self.data['collectors']:
            collector.clear()

    def iterate(self):
        self.system.iterate()
        self.update()

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
                    self.load_checkpoint(self.most_recent_check)
                else:
                    raise Exception("Something went wrong.")

        self.status = "post-traverse"
        if rank == 0:
            print("Done!")
        if checkpointCondition():
            self.checkpoint()
        self.status = "ready"

    def load_checkpoint(self, loadStep):

        if rank == 0:
            print("Loading checkpoint...")

        stepStr = str(loadStep).zfill(8)

        checkpointFile = os.path.join(self.path, stepStr)

        utilities.varsOnDisk(
            self.system.varsOfState,
            checkpointFile,
            'load',
            blackhole = self.system.blackhole,
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

        if rank == 0:
            print("Checkpoint successfully loaded.")

    def reset(self):
        for varName in sorted(self.system.varsOfState):
            var = self.system.varsOfState[varName]
            IC = self.initial[varName]
            IC.apply(var)
        self.system.step.value = 0
        self.system.modeltime.value = 0.
        self.system.solve()
        self.update()
        self.status = "ready"