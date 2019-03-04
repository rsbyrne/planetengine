
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

def load_frame(loadpath):

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
        )

    return frame

class Frame:

    def __init__(self,
            system,
            observer,
            initial,
            outputPath = '',
            instanceID = None,
            ):

        self.system = system
        self.initial = initial.attach(system)
        self.observer = observer.attach(system)

        self.outputPath = outputPath

        self.timestamp = planetengine.utilities.timestamp()

        if instanceID == None:
            self.instanceID = 'test' + self.timestamp
        else:
            self.instanceID = instanceID

        self.path = os.path.join(outputPath, self.instanceID)

#         self.step = fn.misc.constant(0)
#         self.modeltime = fn.misc.constant(0.)

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.system.step,
            varsOfState = self.system.varsOfState,
            figs = self.observer.figs,
            dataCollectors = self.observer.data['collectors'],
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

        self.reset()
        self.allDataRefreshed = False
        self.allDataCollected = False
        self.status = "ready"

        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value

    def checkpoint(self):
        if not self.allDataCollected:
            self.all_collect()
        self.checkpointer.checkpoint()

    def update(self):
        for projector in self.observer.projectors:
            projector.solve()
        self.step = self.system.step.value
        self.modeltime = self.system.modeltime.value
        self.allDataRefreshed = False
        self.allDataCollected = False

    def all_analyse(self):
        for analyser in self.observer.data['analysers']:
            analyser.analyse()
        self.allDataRefreshed = True

    def report(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for analyser in self.observer.data['analysers']:
            analyser.report()
        for figname in self.observer.figs:
            if uw.rank() == 0:
                print(figname)
            self.observer.figs[figname].show()

    def reset(self):
        self.initial.apply()
        self.update()

    def all_collect(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for collector in self.observer.data['collectors']:
            collector.collect()
        self.allDataCollected = True

    def iterate(self):
        self.system.iterate()
        self.update()

    def traverse(self, stopCondition,
            collectCondition = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            ):

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

    def load_checkpoint(self, step):

        stepStr = str(step).zfill(8)

        checkpointFile = os.path.join(self.path, stepStr)

        for item in self.system.varsOfState:
            for varName, var in item[0]:
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

        self.system.step.value = step #int(dataDict['step'])
        self.system.modeltime.value = float(dataDict['modeltime'])

        self.system.solve()
        self.update()

        if uw.rank() == 0:
            print("Checkpoint successfully loaded.")