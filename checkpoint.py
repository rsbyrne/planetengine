import numpy as np
import os
import shutil
import json

from . import disk
from .utilities import message

from . import paths
from . import _built as built

from . import mpi

class Checkpointer:

    def __init__(
            self,
            saveVars = None,
            builts = None,
            figs = None,
            collectors = None,
            step = None,
            modeltime = None,
            info = {},
            framescript = None,
            instanceID = None,
            prefix = 'pe',
            preFn = None,
            postFn = None
            ):

        self.figs = figs
        self.collectors = collectors
        self.saveVars = saveVars
        self.step = step
        self.modeltime = modeltime
        self.builts = builts
        self.stamps = built.make_stamps(builts)
        self.info = info
        self.framescript = framescript
        self.preFn = preFn
        self.postFn = postFn
        if instanceID is None:
            self.instanceID = prefix + '_' + self.stamps['all'][1]
        else:
            self.instanceID = instanceID

    def checkpoint(
            self,
            outputPath = None,
            collect = True,
            clear = True,
            archive = None,
            preFn = None,
            postFn = None
            ):

        if outputPath is None:
            outputPath = paths.defaultPath

        with disk.expose(
                    self.instanceID,
                    outputPath,
                    archive
                    ) \
                as filemanager:

            if not preFn is None:
                preFn()
            if not self.preFn is None:
                self.preFn()

            self._checkpoint(filemanager.path, collect, clear)

            if not self.postFn is None:
                self.postFn()
            if not postFn is None:
                postFn()

    def _checkpoint(self, path, collect, clear):

        message("Attempting to checkpoint...")

        step = self.step()
        modeltime = self.modeltime()

        stamps_exist = False
        if mpi.rank == 0:
            stamps_exist = os.path.isfile(
                os.path.join(path, 'stamps.json')
                )
        stamps_exist = mpi.comm.bcast(stamps_exist, root = 0)
        # mpi.barrier()

        message("Checking for pre-existing frame on disk...")

        if stamps_exist:

            loadstamps = disk.load_json('stamps', path)
            if not loadstamps == self.stamps:
                raise Exception("You are trying to save a model in a different model's directory!")

            message("Pre-existing directory for this model has been found. Continuing...")

            coldstart = False

        else:

            message("No pre-existing directory for this model found. Making a new one...")

            coldstart = True

            if mpi.rank == 0:
                if not os.path.isdir(path):
                    os.makedirs(path)
                assert os.path.isdir(path)
            # mpi.barrier()

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

        if mpi.rank == 0:
            if os.path.isdir(checkpointDir):
                # message('Checkpoint directory found: removing')
                shutil.rmtree(checkpointDir)
                assert not os.path.isdir(checkpointDir)
            # message('Making checkpoint directory.')
            os.makedirs(checkpointDir)
            assert os.path.isdir(checkpointDir)
        # mpi.barrier()

        ## DEBUGGING ###
        message("Saving figures...")
        if not self.figs is None:
            for fig in self.figs:
                fig.save(checkpointDir)
        message("Figures saved.")

        ## DEBUGGING ###
        message("Saving vars of state...")
        if not self.saveVars is None:
            disk.varsOnDisk(self.saveVars, checkpointDir, 'save')
        message("Saved.")

        if collect:
            for collector in self.collectors:
                collector.collect()

        message("Saving snapshot...")
        if mpi.rank == 0:
            if not self.collectors is None:
                for collector in self.collectors:
                    for analyser in collector.analysers:
                        name = analyser.name
                        headerStr = analyser.header
                        dataArray = np.array(analyser.data)
                        assert not None in dataArray
                        filename = os.path.join(checkpointDir, name + "_snapshot" + ".txt")
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
        # mpi.barrier()
        message("Snapshot saved.")

        disk.save_json(modeltime, 'modeltime', checkpointDir)

        disk.save_json(self.stamps, 'stamps', checkpointDir)

        message("Saving datasets...")
        if not self.collectors is None:
            for collector in self.collectors:
                for row in collector.out():
                    if mpi.rank == 0:
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
                if clear:
                    collector.clear()
                    # mpi.barrier()

        message("Datasets saved.")

        if mpi.rank == 0:
            assert os.path.isfile(os.path.join(checkpointDir, 'stamps.json')), \
                "The files did not get saved for some reason!"
        # mpi.barrier()

        message("Checkpointed!")
