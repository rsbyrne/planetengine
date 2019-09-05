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

from . import utilities
from .utilities import message

class Checkpointer:

    def __init__(
            self,
            stamps,
            varsOfState = None,
            scripts = None,
            figs = None,
            dataCollectors = None,
            # params = None,
            # configs = None,
            # options = None,
            inputs = {}
            step = None,
            modeltime = None,
            inFrames = [],
            ):

        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.varsOfState = varsOfState
        self.step = step
        self.modeltime = modeltime
        # self.params = params
        # self.configs = configs
        # self.options = options
        self.inputs = inputs
        self.stamps = stamps
        self.inFrames = inFrames

    def checkpoint(
            self,
            path = 'test',
            ):

        coldstart = True

        if uw.mpi.rank == 0:

            if os.path.isfile(os.path.join(path, 'stamps.json')):

                with open(os.path.join(path, 'stamps.json')) as json_file:
                    loadstamps = json.load(json_file)
                if not loadstamps == self.stamps:
                    raise Exception("You are trying to save a model in a different model's directory!")
                else:
                    message("Pre-existing directory for this model has been found. Continuing...")

                coldstart = False

        coldstart = uw.mpi.comm.bcast(coldstart, root = 0)

        if coldstart:

            if uw.mpi.rank == 0:

                message("No pre-existing directory for this model found. Making a new one...")

                if not os.path.isdir(path):
                    os.makedirs(path)

                if not self.scripts is None:
                    for scriptname in self.scripts:
                        scriptpath = self.scripts[scriptname]
                        tweakedpath = os.path.splitext(scriptpath)[0] + ".py"
                        newpath = os.path.join(path, "_" + scriptname + ".py")
                        shutil.copyfile(tweakedpath, newpath)

                for dictname, inputDict in self.inputs.items():
                    filename = os.path.join(path, dictname + '.json')
                    with open(filename, 'w') as file:
                         json.dump(inputDict, filename)

                # paramsFilename = os.path.join(path, 'params.json')
                # with open(paramsFilename, 'w') as file:
                #      json.dump(self.params, file)
                #
                # configsFilename = os.path.join(path, 'configs.json')
                # with open(configsFilename, 'w') as file:
                #      json.dump(self.configs, file)
                #
                # optionsFilename = os.path.join(path, 'options.json')
                # with open(optionsFilename, 'w') as file:
                #      json.dump(self.options, file)
                #
                stampFilename = os.path.join(path, 'stamps.json')
                with open(stampFilename, 'w') as file:
                     json.dump(self.stamps, file)

            for inFrame in self.inFrames:
                inFrame.checkpoint(
                    os.path.join(path, inFrame.hashID),
                    archive_remote = False
                    )

        message("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        checkpointDir = os.path.join(path, stepStr)

        if uw.mpi.rank == 0:
            if os.path.isdir(checkpointDir):
                message('Checkpoint directory found: removing')
                shutil.rmtree(checkpointDir)
            else:
                message('Making checkpoint directory.')
                os.makedirs(checkpointDir)

        message("Saving figures...")
        if not self.figs is None:
            for fig in self.figs:
                fig.save(checkpointDir)
        message("Figures saved.")

        message("Saving vars of state...")
        if not self.varsOfState is None:
            utilities.varsOnDisk(self.varsOfState, checkpointDir, 'save')
        message("Saved.")

        message("Saving snapshot...")
        if uw.mpi.rank == 0:
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for analyser in dataCollector.analysers:
                        name = analyser.name
                        headerStr = analyser.header
                        dataArray = [analyser.data,]
                        filename = os.path.join(checkpointDir, name + "_snapshot" + ".txt")
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
        message("Snapshot saved.")

        message("Saving modeltime...")
        if uw.mpi.rank == 0:
            modeltime_filepath = os.path.join(
                checkpointDir,
                'modeltime.json'
                )
            modeltime = self.modeltime.value
            with open(modeltime_filepath, 'w') as file:
                json.dump(modeltime, file)
        message("Modeltime saved.")

        message("Saving stamps...")
        if uw.mpi.rank == 0:
            filename = os.path.join(checkpointDir, 'stamps.json')
            with open(filename, 'w') as file:
                 json.dump(self.stamps, file)
        message("Stamps saved.")

        message("Saving datasets...")
        if not self.dataCollectors is None:
            for dataCollector in self.dataCollectors:
                for row in dataCollector.out():
                    if uw.mpi.rank == 0:
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
        message("Datasets saved.")

        if uw.mpi.rank == 0:
            assert os.path.isfile(os.path.join(checkpointDir, 'stamps.json')), \
                "The files did not get saved for some reason!"

        message("Checkpointed!")
