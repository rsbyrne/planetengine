
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

def load_model(loadpath):

    outputPath = os.path.dirname(loadpath)
    instanceID = os.path.basename(loadpath)
    
    systemscript = utilities.local_import(os.path.join(loadpath, '_systemscript.py'))
    handlerscript = utilities.local_import(os.path.join(loadpath, '_handlerscript.py'))
    initialscript = utilities.local_import(os.path.join(loadpath, '_initialscript.py'))

    with open(os.path.join(loadpath, 'inputs.txt')) as json_file:  
        inputs = json.load(json_file)
    params = inputs['params']
    options = inputs['options']
    config = inputs['config']

    model = Model(
        systemscript.build(**inputs['params']),
        handlerscript.build(**inputs['options']),
        initialscript.build(**inputs['config']),
        outputPath = os.path.dirname(loadpath),
        instanceID = os.path.basename(loadpath),
        )

    return model

class Model:

    def __init__(self, system, handler, initial,
        outputPath = '',
        instanceID = None,
        ):

        self.system = system
        self.handler = handler
        self.initial = initial
        self.outputPath = outputPath

        self.timestamp = planetengine.utilities.timestamp()

        if instanceID == None:
            self.instanceID = 'test' + self.timestamp
        else:
            self.instanceID = instanceID

        self.path = os.path.join(outputPath, self.instanceID)

        self.step = fn.misc.constant(0)
        self.modeltime = fn.misc.constant(0.)

        self.figs = self.handler.make_figs(system, self.step, self.modeltime)
        self.data = self.handler.make_data(system, self.step, self.modeltime)

        self.checkpointer = planetengine.checkpoint.Checkpointer(
            step = self.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data.collectors,
            scripts = {
                'systemscript': self.system.script,
                'handlerscript': self.handler.script,
                'initialscript': self.initial.script,
                },
            inputs = {
                'params': self.system.inputs,
                'options': self.handler.inputs,
                'config': self.initial.inputs,
                },
            path = self.path,
            )

        self.reset()
        self.allDataRefreshed = False
        self.allDataCollected = False
        self.status = "ready"

    def checkpoint(self):
        if not self.allDataCollected:
            self.all_collect()
        self.checkpointer.checkpoint()

    def update(self):
        self.allDataRefreshed = False
        self.allDataCollected = False

    def all_analyse(self):
        for analyser in self.data.analysers:
            analyser.analyse()
        self.allDataRefreshed = True

    def report(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for analyser in self.data.analysers:
            analyser.report()
        for figname in self.figs:
            if uw.rank() == 0:
                print(figname)
            self.figs[figname].show()

    def reset(self):
        self.initial.apply(self.system)
        self.step.value = 0
        self.modeltime.value = 0.
        self.update()

    def all_collect(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for collector in self.data.collectors:
            collector.collect()
        self.allDataCollected = True

    def iterate(self):
        self.modeltime.value += self.system.iterate()
        self.step.value += 1
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
                #for index, collector in enumerate(self.data.collectors):
                    #if type(collectConditions) == list:
                        #condition = collectConditions[index]()
                    #else:
                        #condition = collectConditions()
                    #if condition:
                        #collector.collect()

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

        self.step.value = step #int(dataDict['step'])
        self.modeltime.value = float(dataDict['modeltime'])

        self.system.solve()
        self.update()

        if uw.rank() == 0:
            print("Checkpoint successfully loaded.")
