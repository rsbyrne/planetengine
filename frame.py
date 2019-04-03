
# coding: utf-8

# In[1]:


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
    
    systemscript = utilities.local_import(os.path.join(loadpath, '_systemscript.py'))
    observerscript = utilities.local_import(os.path.join(loadpath, '_observerscript.py'))
    initialscript = utilities.local_import(os.path.join(loadpath, '_initialscript.py'))

    with open(os.path.join(loadpath, 'inputs.txt')) as json_file:  
        inputs = json.load(json_file)
    params = inputs['params']
    options = inputs['options']
    config = inputs['config']

    with open(os.path.join(loadpath, 'stamps.txt')) as json_file:
        stamps = json.load(json_file)

    frame = Frame(
        system = systemscript.build(**inputs['params']),
        observer = observerscript.build(**inputs['options']),
        initial = initialscript.build(**inputs['config']),
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

        self.outputPath = outputPath

        if _stamps == None:
            self.stamps = {
                'paramstamp': utilities.dictstamp(system.inputs),
                'optionstamp': utilities.dictstamp(observer.inputs),
                'configstamp': utilities.dictstamp(initial.inputs),
                'systemstamp': utilities.scriptstamp(system.script),
                'observerstamp': utilities.scriptstamp(observer.script),
                'initialstamp': utilities.scriptstamp(initial.script),
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

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.system.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data['collectors'],
            scripts = {
                'systemscript': self.system.script,
                'observerscript': self.observer.script,
                'initialscript': self.initial.script,
                },
            inputs = {
                'params': self.system.inputs,
                'options': self.observer.inputs,
                'config': self.initial.inputs,
                },
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
        self.initial.apply(self.system)
        self.update()
        self.status = "ready"