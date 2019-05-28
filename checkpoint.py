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
            stamps,
            varsOfState = None,
            scripts = None,
            figs = None,
            dataCollectors = None,
            inputs = None,
            step = None,
            inFrames = [],
            ):

        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.varsOfState = varsOfState
        self.step = step
        self.inputs = inputs
        self.stamps = stamps
        self.inFrames = inFrames

    def checkpoint(
            self,
            path = 'test',
            saveData = True
            ):

        coldstart = True

        if rank == 0:

            if os.path.isfile(os.path.join(path, 'stamps.txt')):

                with open(os.path.join(path, 'stamps.txt')) as json_file:
                    loadstamps = json.load(json_file)
                if not loadstamps == self.stamps:
                    raise Exception("You are trying to save a model in a different model's directory!")
                else:
                    planetengine.message("Pre-existing directory for this model has been found. Continuing...")

                coldstart = False

        coldstart = comm.bcast(coldstart, root = 0)

        if coldstart:

            if rank == 0:

                planetengine.message("No pre-existing directory for this model found. Making a new one...")

                if not os.path.isdir(path):
                    os.makedirs(path)

                if not self.scripts is None:
                    for scriptname in self.scripts:
                        scriptpath = self.scripts[scriptname]
                        tweakedpath = os.path.splitext(scriptpath)[0] + ".py"
                        newpath = os.path.join(path, "_" + scriptname + ".py")
                        shutil.copyfile(tweakedpath, newpath)

                inputFilename = os.path.join(path, 'inputs.txt')
                with open(inputFilename, 'w') as file:
                     file.write(json.dumps(self.inputs))

                stampFilename = os.path.join(path, 'stamps.txt')
                with open(stampFilename, 'w') as file:
                     file.write(json.dumps(self.stamps))

            for inFrame in self.inFrames:
                inFrame.checkpoint(
                    os.path.join(path, inFrame.hashID),
                    archive_remote = False
                    )

        planetengine.message("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        checkpointDir = os.path.join(path, stepStr)

        if rank == 0:
            if os.path.isdir(checkpointDir):
                planetengine.message('Checkpoint directory found: removing')
                shutil.rmtree(checkpointDir)
            else:
                planetengine.message('Making checkpoint directory.')
                os.makedirs(checkpointDir)

        planetengine.message("Saving figures...")
        if not self.figs is None:
            for name in self.figs:
                fig = self.figs[name]
                fig.save(os.path.join(checkpointDir, name))
        planetengine.message("Figures saved.")

        planetengine.message("Saving vars of state...")
        if not self.varsOfState is None:
            utilities.varsOnDisk(self.varsOfState, checkpointDir, 'save')
        planetengine.message("Saved.")

        planetengine.message("Saving snapshot...")
        if rank == 0:
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for index, name in enumerate(dataCollector.names):
                        dataArray = dataCollector.datasets[index][-1:]
                        headerStr = dataCollector.headers[index]
                        filename = os.path.join(checkpointDir, name + "_snapshot" + ".txt")
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
        planetengine.message("Snapshot saved.")

        planetengine.message("Saving stamps...")
        if rank == 0:
            filename = os.path.join(checkpointDir, 'stamps.txt')
            with open(filename, 'w') as file:
                 file.write(json.dumps(self.stamps))
        planetengine.message("Stamps saved.")

        if saveData:
            planetengine.message("Saving datasets...")
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for row in dataCollector.clear():
                        if rank == 0:
                            name, headerStr, dataArray = row
                            filename = os.path.join(path, name + '.csv')
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
            planetengine.message("Datasets saved.")

        if rank == 0:
            assert os.path.isfile(os.path.join(checkpointDir, 'stamps.txt')), \
                "The files did not get saved for some reason!"

        planetengine.message("Checkpointed!")