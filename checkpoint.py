import numpy as np
import underworld as uw
import os
import shutil
import json

from . import disk
from .utilities import message

from . import frame
from . import paths
from . import built

class Checkpointer:

    def __init__(
            self,
            saveVars = None,
            builts = None,
            figs = None,
            dataCollectors = None,
            step = None,
            modeltime = None,
            info = {},
            framescript = None,
            ):

        self.figs = figs
        self.dataCollectors = dataCollectors
        self.saveVars = saveVars
        self.step = step
        self.modeltime = modeltime
        self.builts = builts
        self.stamps = built.make_stamps(builts)
        self.info = info
        self.framescript = framescript

    def checkpoint(
            self,
            path = None,
            ):

        if path is None:
            path = paths.defaultPath

        step = self.step()
        modeltime = self.modeltime()

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

                built.save_builtsDir(self.builts, path)

                disk.save_json(self.stamps, 'stamps', path)

                disk.save_json(self.info, 'info', path)

                if not self.framescript is None:
                    disk.save_script(
                        self.framescript, 'framescript', path
                        )

        message("Checkpointing...")

        if step is None:
            stepStr = ""
        else:
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
        if not self.saveVars is None:
            disk.varsOnDisk(self.saveVars, checkpointDir, 'save')
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

        disk.save_json(modeltime, 'modeltime', checkpointDir)

        disk.save_json(self.stamps, 'stamps', checkpointDir)

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
