
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

import planetengine
from planetengine import utilities

def load_frame(loadpath, loadStep = 0):

    outputPath = os.path.dirname(loadpath)
    instanceID = os.path.basename(loadpath)
    
    systemscript = utilities.local_import(os.path.join(loadpath, '_systemscript.py'))
    observerscript = utilities.local_import(os.path.join(loadpath, '_observerscript.py'))
    initialscript = utilities.local_import(os.path.join(loadpath, '_initialscript.py'))

    with open(os.path.join(loadpath, 'inputs.txt')) as json_file:  
        inputs = json.load(json_file)
    params = inputs['params']
    options = inputs['options']
    config = inputs['config']

    frame = Frame(
        system = systemscript.build(**inputs['params']),
        observer = observerscript.build(**inputs['options']),
        initial = initialscript.build(**inputs['config']),
        outputPath = os.path.dirname(loadpath),
        instanceID = os.path.basename(loadpath),
        loadStep = loadStep,
        )

    return frame

class Frame:

    def __init__(self,
            system,
            observer,
            initial,
            outputPath = '',
            instanceID = None,
            loadStep = 0,
            ):

        self.outputPath = outputPath

        self.timestamp = planetengine.utilities.timestamp()

        if instanceID == None:
            self.instanceID = 'test' + self.timestamp
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
            path = self.path,
            )

        self.allDataRefreshed = False
        self.allDataCollected = False
        self.status = "ready"

        if not loadStep == 0:

            if uw.rank() == 0:
                print("Loading checkpoint...")

            stepStr = str(loadStep).zfill(8)

            checkpointFile = os.path.join(self.path, stepStr)

            for item in self.system.varsOfState:
                varList, substratePair = item
                substrateName, substrate = substratePair
                loadName = os.path.join(checkpointFile, substrateName + '.h5')
                if type(substrate) == uw.swarm.Swarm:
                    with substrate.deform_swarm():
                        substrate.particleCoordinates.data[:] = [0., 0.]
                substrate.load(loadName)
                for varName, var in varList:
                    loadName = os.path.join(checkpointFile, varName + '.h5')
                    var.load(loadName)

            snapshot = os.path.join(checkpointFile, 'zerodData_snapshot.csv') ### TO DO: CHANGE THIS
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

            if uw.rank() == 0:
                print("Checkpoint successfully loaded.")

        else:
            if uw.rank() == 0:
                print("Applying initial conditions...")

            self.initial.apply(self.system)

            if uw.rank() == 0:
                print("Initial conditions applied.")

        self.update()

    def checkpoint(self):
        if not self.allDataCollected:
            self.all_collect()
        self.checkpointer.checkpoint()

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
            if uw.rank() == 0:
                print(figname)
            self.figs[figname].show()

    def all_collect(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for collector in self.data['collectors']:
            collector.collect()
        self.allDataCollected = True

    def iterate(self):
        self.system.iterate()
        self.update()

    def traverse(self, stopCondition,
            collectCondition = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            startStep = None,
            ):

        if not startStep == None:
            self.load(startStep)

        self.status = "pre-traverse"

        if checkpointCondition():
            self.checkpoint()

        while not stopCondition():

            self.status = "traversing"
            self.iterate()

            if checkpointCondition():
                self.checkpoint()
            elif collectCondition():
                self.all_collect()
            if reportCondition():
                self.report()

        self.status = "post-traverse"

        if checkpointCondition():
            self.checkpoint()

        self.status = "ready"

    def load(self, step):
        self.__init__(
            self.system,
            self.observer,
            self.initial,
            outputPath = self.outputPath,
            instanceID = self.instanceID,
            loadStep = step,
            )

    def reset(self):
        self.load(0)