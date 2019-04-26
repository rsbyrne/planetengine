
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
import tar

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

import planetengine
from planetengine import utilities

class Checkpointer:

    def __init__(
            self,
            varsOfState = None,
            outputPath = '',
            instanceID = 'test',
            scripts = None,
            figs = None,
            dataCollectors = None,
            inputs = None,
            step = None,
            stamps = None,
            archive = False,
            inFrames = {},
            ):

        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.varsOfState = varsOfState
        self.step = step
        self.inputs = inputs
        self.outputPath = outputPath
        self.instanceID = instanceID
        self.path = os.path.join(self.outputPath, self.instanceID)
        self.tarpath = self.path + '.tar.gz'
        self.stamps = stamps
        self.archive = archive
        self.inFrames = inFrames

        self.inFrame_checkpointers = []
        for hashID, inFrame in sorted(self.inFrames.items()):
            inFrame.all_collect()
            inFrame_checkpointer = planetengine.checkpoint.Checkpointer(
                step = inFrame.system.step,
                varsOfState = inFrame.system.varsOfState,
                figs = inFrame.figs,
                dataCollectors = inFrame.data['collectors'],
                scripts = inFrame.scripts,
                inputs = inFrame.inputs,
                stamps = inFrame.stamps,
                outputPath = self.path,
                instanceID = hashID,
                inFrames = inFrame.inFrames,
                )
            self.inFrame_checkpointers.append(inFrame_checkpointer)

    def checkpoint(self):

        if rank == 0:
            if self.archive:
                if os.path.isfile(self.tarpath):
                    if not os.path.isdir(self.path):
                        print("Tar found - unarchiving...")
                        with tarfile.open(self.tarpath) as tar:
                            tar.extractall()
                        print("Unarchived.")
                        if not os.path.isdir(self.path):
                            raise Exception("Archive contained the wrong model file somehow.")
                    else:
                        raise Exception("Conflicting archive and directory found.")

        if os.path.isdir(self.path):
            
            if rank == 0:

                if not os.path.isfile(os.path.join(self.path, 'stamps.txt')):
                    raise Exception("No stamps file found. Aborting.")
                else:
                    with open(os.path.join(self.path, 'stamps.txt')) as json_file:
                        loadstamps = json.load(json_file)
                    if not loadstamps == self.stamps:
                        raise Exception("You are trying to save a model in a different model's directory!")
                    else:
                        print("Pre-existing directory for this model has been found. Continuing...")

        else:

            if rank == 0:

                print("No pre-existing directory for this model found. Making a new one...")

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

                stampFilename = os.path.join(self.path, 'stamps.txt')
                with open(stampFilename, 'w') as file:
                     file.write(json.dumps(self.stamps))

            if len(self.inFrame_checkpointers) > 0:
                if rank == 0:
                    print("Saving inFrames...")
                for checkpointer in self.inFrame_checkpointers:
                    checkpointer.checkpoint()
                if rank == 0:
                    print("inFrames saved.")

        if rank == 0:
            if self.archive:
                if os.path.isfile(self.tarpath):
                    print("Deleting unarchived archive...")
                    os.remove(self.tarpath)
                    print("Deleted.")

        if rank == 0:
            print("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        self.checkpointDir = os.path.join(self.path, stepStr)

        if os.path.isdir(self.checkpointDir):
            if rank == 0:
                print('Checkpoint directory found: skipping.')
            return None
        else:
            if rank == 0:
                os.makedirs(self.checkpointDir)

        if rank == 0:
            print("Saving figures...")
        if not self.figs is None:
            for name in self.figs:
                fig = self.figs[name]
                fig.save(os.path.join(self.checkpointDir, name))
        if rank == 0:
            print("Saved.")

        if rank == 0:
            print("Saving vars of state...")
        if not self.varsOfState is None:
            utilities.varsOnDisk(self.varsOfState, self.checkpointDir, 'save')
        if rank == 0:
            print("Saved.")

        if rank == 0:
            print("Saving snapshot...")
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for index, name in enumerate(dataCollector.names):
                        dataArray = dataCollector.datasets[index][-1:]
                        headerStr = dataCollector.headers[index]
                        filename = os.path.join(self.checkpointDir, name + "_snapshot" + ".txt")
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
            print("Saved.")

        if rank == 0:
            print("Saving stamps...")
            if not self.stamps is None:
                filename = os.path.join(self.checkpointDir, 'stamps.txt')
                with open(filename, 'w') as file:
                     file.write(json.dumps(self.stamps))
            print("Saved.")

        if rank == 0:
            print("Saving datasets...")
        if not self.dataCollectors is None:
            for dataCollector in self.dataCollectors:
                for row in dataCollector.clear():
                    if rank == 0:
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
        if rank == 0:
            print("Saved.")

        if self.archive:
            if rank == 0:
                print("Archiving...")
                with tarfile.open(self.tarpath, 'w:gz') as tar:
                    tar.add(self.path)
                print("Archived.")
                print("Deleting superfluous files...")
                shutil.rmtree(self.path)
                print("Done.")

        if rank == 0:
            print("Checkpointed!")
