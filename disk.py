import os
import json
import shutil
import tarfile
import importlib
import underworld as uw
from . import utilities
from .utilities import message
from .functions import _basetypes
from . import paths

from . import mpi

import underworld as uw

def disk_state(path):
    path = os.path.splitext(path)[0]
    tarpath = path + '.tar.gz'
    diskstate = ''
    if mpi.rank == 0:
        isfile = os.path.isfile(tarpath)
        isdir = os.path.isdir(path)
        assert not (isfile and isdir)
        if isfile:
            diskstate = 'tar'
        elif isdir:
            diskstate = 'dir'
        else:
            diskstate = 'clean'
    diskstate = mpi.comm.bcast(diskstate, root = 0)
    return diskstate

def save_json(jsonObj, name, path):
    if mpi.rank == 0:
        jsonFilename = os.path.join(path, name + '.json')
        with open(jsonFilename, 'w') as file:
             json.dump(jsonObj, file)
    # mpi.barrier()

def load_json(jsonName, path):
    filename = jsonName + '.json'
    jsonDict = {}
    if mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            jsonDict = json.load(json_file)
    jsonDict = mpi.comm.bcast(jsonDict, root = 0)
    return jsonDict

def local_import(filepath):

    modname = os.path.basename(filepath)

    spec = importlib.util.spec_from_file_location(
        modname,
        filepath,
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def save_script(script, name, path):
    if mpi.rank == 0:
        tweakedPath = os.path.splitext(script)[0] + ".py"
        newPath = os.path.join(path, name + ".py")
        shutil.copyfile(tweakedPath, newPath)
    # mpi.barrier()

def load_script(name, path):
    scriptPath = os.path.join(path, name) + '.py'
    scriptModule = local_import(
        scriptPath
        )
    return scriptModule

def expose_tar(path):

    assert disk_state(path) == 'tar'

    tarpath = path + '.tar.gz'

    message("Tar found - unarchiving...")
    if mpi.rank == 0:
        with tarfile.open(tarpath) as tar:
            tar.extractall(path)
        assert os.path.isdir(path), \
            "Archive contained the wrong model file somehow."
        os.remove(tarpath)

    assert disk_state(path) == 'dir'

    message("Unarchived.")

def varsOnDisk(saveVars, checkpointDir, mode = 'save', blackhole = [0., 0.]):
    substrates = []
    substrateNames = []
    substrateHandles = {}
    extension = '.h5'

    for varName, var in sorted(saveVars.items()):

        if type(var) == _basetypes.Variable:
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
