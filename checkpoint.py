
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

class Checkpointer:

    def __init__(
            self,
            varsOfState = None,
            path = '',
            scripts = None,
            figs = None,
            dataCollectors = None,
            inputs = None,
            step = None,
            ):

        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.varsOfState = varsOfState
        self.step = step
        self.inputs = inputs
        self.path = path

    def checkpoint(self):

        if uw.rank() == 0:
            if not os.path.isdir(self.path):
                os.makedirs(self.path)

                if not self.scripts is None:
                    for scriptname in self.scripts:
                        path = self.scripts[scriptname]
                        tweakedpath = os.path.splitext(path)[0] + ".py"
                        newpath = os.path.join(self.path, "_" + scriptname + ".py")
                        shutil.copyfile(tweakedpath, newpath)

                inputFilename = os.path.join(self.path, 'inputs.txt')
                with open(inputFilename, 'w') as file:
                     file.write(json.dumps(self.inputs))

        if uw.rank() == 0:
            print("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        self.checkpointDir = os.path.join(self.path, stepStr)

        if os.path.isdir(self.checkpointDir):
            if uw.rank() == 0:
                print('Checkpoint directory found: skipping.')
            return None
        else:
            if uw.rank() == 0:
                os.makedirs(self.checkpointDir)

        if uw.rank() == 0:
            print("Saving figures...")
        if not self.figs is None:
            for name in self.figs:
                fig = self.figs[name]
                fig.save(os.path.join(self.checkpointDir, name))
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Saving vars of state...")
        if not self.varsOfState is None:
            utilities.varsOnDisk(self.varsOfState, self.checkpointDir, 'save')
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Saving snapshot...")
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for index, name in enumerate(dataCollector.names):
                        dataArray = dataCollector.datasets[index][-1:]
                        headerStr = dataCollector.headers[index]
                        filename = os.path.join(self.checkpointDir, name + "_snapshot" + ".csv")
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
            print("Saved.")

        if uw.rank() == 0:
            print("Saving datasets...")
        if not self.dataCollectors is None:
            for dataCollector in self.dataCollectors:
                for row in dataCollector.clear():
                    if uw.rank() == 0:
                        name, headerStr, dataArray = row
                        filename = os.path.join(self.path, name + '.csv')
                        if not type(dataArray) == type(None):
                            with open(filename, 'ab') as openedfile:
                                fileSize = os.stat(filename).st_size
                                if fileSize == 0:
                                    header = headerStr
                                else:
                                    header = ''
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = header
                                    )
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Checkpointed!")
