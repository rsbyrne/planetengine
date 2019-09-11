import os
import json
import shutil
import tarfile
import underworld as uw
from . import utilities
from .utilities import message
from .functions import Variable

def save_json(jsonObj, name, path):
    if uw.mpi.rank == 0:
        jsonFilename = os.path.join(path, name + '.json')
        with open(jsonFilename, 'w') as file:
             json.dump(jsonObj, file)

def load_json(jsonName, path):
    filename = jsonName + '.json'
    jsonDict = {}
    if uw.mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            jsonDict = json.load(json_file)
    jsonDict = uw.mpi.comm.bcast(jsonDict, root = 0)
    return jsonDict

def save_script(script, name, path):
    if uw.mpi.rank == 0:
        tweakedPath = os.path.splitext(script)[0] + ".py"
        newPath = os.path.join(path, name + ".py")
        shutil.copyfile(tweakedPath, newPath)

def load_script(name, path):
    scriptPath = os.path.join(path, name) + '.py'
    scriptModule = utilities.local_import(
        scriptPath
        )
    return scriptModule

def expose_tar(path):

    tarpath = path + '.tar.gz'

    print(path)

    if uw.mpi.rank == 0:
        assert os.path.isdir(path) or os.path.isfile(tarpath), \
            "No model found at that directory!"

    if uw.mpi.rank == 0:
        if os.path.isfile(tarpath):
            assert not os.path.isdir(path), \
                "Conflicting archive and directory found."
            message("Tar found - unarchiving...")
            with tarfile.open(tarpath) as tar:
                tar.extractall(path)
            message("Unarchived.")
            assert os.path.isdir(path), \
                "Archive contained the wrong model file somehow."
            os.remove(tarpath)

def varsOnDisk(saveVars, checkpointDir, mode = 'save', blackhole = [0., 0.]):
    substrates = []
    substrateNames = []
    substrateHandles = {}
    extension = '.h5'

    for varName, var in sorted(saveVars.items()):

        if type(var) == Variable:
            var.update()
            var = var.var

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            substrate = var.mesh
            substrateName = 'mesh'
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            substrate = var.swarm
            substrateName = 'swarm'
        else:
            raise Exception('Variable type not recognised.')

        if not substrate in substrates:
            if substrateName in substrateNames:
                nameFound = False
                suffix = 0
                while not nameFound:
                    adjustedSubstrateName = substrateName + '_' + str(suffix)
                    if not adjustedSubstrateName in substrateNames:
                        substrateName = adjustedSubstrateName
                        nameFound = True
                    else:
                        suffix += 1
            substrateNames.append(substrateName)

            if mode == 'save':
                message("Saving substrate to disk: " + substrateName)
                handle = substrate.save(
                    os.path.join(
                        checkpointDir,
                        substrateName + extension
                        )
                    )
                # substrateHandles[substrateName] = handle
                substrateHandles[substrate] = handle
            elif mode == 'load':
                message("Loading substrate from disk: " + substrateName)
                if type(substrate) == uw.swarm.Swarm:
                    with substrate.deform_swarm():
                        substrate.particleCoordinates.data[:] = blackhole
                    assert substrate.particleGlobalCount == 0
                substrate.load(os.path.join(checkpointDir, substrateName + extension))
            else:
                raise Exception("Disk mode not recognised.")
            substrates.append(substrate)

        else:
            if mode == 'save':
                handle = substrateHandles[substrate]

        if mode == 'save':
            message("Saving var to disk: " + varName)
            var.save(os.path.join(checkpointDir, varName + extension), handle)
        elif mode == 'load':
            message("Loading var from disk: " + varName)
            var.load(os.path.join(checkpointDir, varName + extension))
        else:
            raise Exception("Disk mode not recognised.")
