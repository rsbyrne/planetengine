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
            path = 'test',
            scripts = None,
            figs = None,
            dataCollectors = None,
            inputs = None,
            step = None,
#             archive = False,
            inFrames = {},
            ):

        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.varsOfState = varsOfState
        self.step = step
        self.inputs = inputs
        self.path = path
#         self.tarpath = self.path + '.tar.gz'
        self.stamps = stamps
#         self.archive = archive
        self.inFrames = inFrames

        self.inFrame_checkpointers = []
        for hashID, inFrame in sorted(self.inFrames.items()):
            inFrame.all_collect()
            inFrame_checkpointer = planetengine.checkpoint.Checkpointer(
                stamps = inFrame.stamps,
                step = inFrame.system.step,
                varsOfState = inFrame.system.varsOfState,
                figs = inFrame.figs,
                dataCollectors = inFrame.data['collectors'],
                scripts = inFrame.scripts,
                inputs = inFrame.inputs,
                path = os.path.join(self.path, hashID),
                inFrames = inFrame.inFrames,
                )
            self.inFrame_checkpointers.append(inFrame_checkpointer)

    def checkpoint(self):

#         if self.archive:
#             if rank == 0:
#                 if os.path.isfile(self.tarpath):
#                     if not os.path.isdir(self.path):
#                         print("Tar found - unarchiving...")
#                         with tarfile.open(self.tarpath) as tar:
#                             tar.extractall()
#                         print("Unarchived.")
#                         if not os.path.isdir(self.path):
#                             raise Exception("Archive contained the wrong model file somehow.")
#                     else:
#                         raise Exception("Conflicting archive and directory found.")

        if os.path.isfile(os.path.join(self.path, 'stamps.txt')):

            if rank == 0:

                with open(os.path.join(self.path, 'stamps.txt')) as json_file:
                    loadstamps = json.load(json_file)
                if not loadstamps == self.stamps:
                    raise Exception("You are trying to save a model in a different model's directory!")
                else:
                    planetengine.message("Pre-existing directory for this model has been found. Continuing...")

        else:

            if rank == 0:

                planetengine.message("No pre-existing directory for this model found. Making a new one...")

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
                planetengine.message("Saving inFrames...")
                for checkpointer in self.inFrame_checkpointers:
                    checkpointer.checkpoint()
                planetengine.message("inFrames saved.")

#         if rank == 0:
#             if self.archive:
#                 if os.path.isfile(self.tarpath):
#                     planetengine.message("Deleting unarchived archive...")
#                     os.remove(self.tarpath)
#                     planetengine.message("Deleted.")

        planetengine.message("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        checkpointDir = os.path.join(self.path, stepStr)

        if os.path.isdir(checkpointDir):
            planetengine.message('Checkpoint directory found: skipping.')
            return None
        else:
            if rank == 0:
                os.makedirs(checkpointDir)

        planetengine.message("Saving figures...")
        if not self.figs is None:
            for name in self.figs:
                fig = self.figs[name]
                fig.save(os.path.join(checkpointDir, name))
        planetengine.message("Saved.")

        planetengine.message("Saving vars of state...")
        if not self.varsOfState is None:
            utilities.varsOnDisk(self.varsOfState, checkpointDir, 'save')
        planetengine.message("Saved.")

        if rank == 0:
            planetengine.message("Saving snapshot...")
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
            print("Saved.")

        if rank == 0:
            planetengine.message("Saving stamps...")
            filename = os.path.join(checkpointDir, 'stamps.txt')
            with open(filename, 'w') as file:
                 file.write(json.dumps(self.stamps))
            planetengine.message("Saved.")

        planetengine.message("Saving datasets...")
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
        planetengine.message("Saved.")

        assert os.path.isfile(os.path.join(checkpointDir, 'stamps.txt')), \
            "The files did not get saved for some reason!"

#         if self.archive:
#             if rank == 0:
#                 planetengine.message("Archiving...")
#                 with tarfile.open(self.tarpath, 'w:gz') as tar:
#                     tar.add(self.path)
#                 planetengine.message("Archived.")
#                 planetengine.message("Deleting superfluous files...")
#                 shutil.rmtree(self.path)
#                 planetengine.message("Done.")

#             assert os.path.isfile(self.tarpath), \
#                 "The archive should have saved, but we can't find it!"

        planetengine.message("Checkpointed!")