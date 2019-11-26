import numpy as np
import time
import os

import underworld as uw
from underworld import function as _fn
from underworld.function._function import Function as UWFn

from . import paths
from . import mpi

def message(*args):
    for arg in args:
        if mpi.rank == 0:
            print(arg)

def log(text, outputPath = None, outputName = 'diaglog.txt'):
    if outputPath == None:
        outputPath = paths.defaultPath

    if mpi.rank == 0:
        filename = os.path.join(outputPath, outputName)
        if not os.path.exists(outputPath):
            os.mkdir(outputPath)
        if os.path.isfile(filename):
            file = open(filename, 'a')
        else:
            file = open(filename, 'w')
        file.write(text)
        file.write('\n')
        file.close()
    # mpi.barrier()

def get_substrates(var):
    if type(var) == uw.mesh._meshvariable.MeshVariable:
        meshes = [var.mesh,]
        swarms = []
    elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
        swarm = var.swarm
        mesh = swarm.mesh
        meshes = [mesh,]
        swarms = [swarm,]
    elif isinstance(var, UWFn):
        underlying = list(var._underlyingDataItems)
        meshes = []
        swarms = []
        for item in underlying:
            under_meshes, under_swarms = get_substrates(item)
            meshes.extend(under_meshes)
            swarms.extend(under_swarms)
        meshes = list(set(meshes))
        swarms = list(set(swarms))
    elif isinstance(var, uw.mesh.FeMesh):
        meshes = [var,]
        swarms = []
    elif isinstance(var, uw.swarm.Swarm):
        meshes = [var.mesh,]
        swarms = [var,]
    else:
        raise Exception("Input not recognised.")
    meshes = list(sorted(meshes))
    swarms = list(sorted(swarms))
    return meshes, swarms

def get_prioritySubstrate(var):
    meshes, swarms = get_substrates(var)
    if len(swarms) > 0:
        substrate = swarms[0]
    elif len(meshes) > 0:
        substrate = meshes[0]
    else:
        substrate = None
    return substrate

def get_mesh(var):
    meshes, swarms = get_substrates(var)
    if len(meshes) > 0:
        return meshes[0]
    else:
        raise Exception("No mesh detected.")

def get_sampleData(var):
    substrate = get_prioritySubstrate(var)
    if substrate is None:
        evalCoords = None
    else:
        evalCoords = substrate.data[0:1]
    sample_data = var.evaluate(evalCoords)
    return sample_data

def get_varDim(var):
    sample_data = get_sampleData(var)
    varDim = sample_data.shape[-1]
    return varDim

# def get_valSets(array):
#     valSets = []
#     assert len(array.shape) == 2
#     for dimension in array.T:
#         localVals = set(dimension)
#         for item in list(localVals):
#             if math.isnan(item):
#                 localVals.remove(item)
#         allValsGathered = mpi.comm.allgather(localVals)
#         valSet = {val.item() for localVals in allValsGathered for val in localVals}
#         valSets.append(valSet)
#     return valSets

def get_scales(array, valSets = None):
    if valSets is None:
        array = np.array(array)
        array = array.T
        outList = []
        for component in array:
            minVal = np.nanmin(component)
            maxVal = np.nanmax(component)
            minVals = mpi.comm.allgather(minVal)
            maxVals = mpi.comm.allgather(maxVal)
            minVals = [val for val in minVals if val < np.inf]
            maxVals = [val for val in maxVals if val < np.inf]
            assert len(minVals) > 0
            assert len(maxVals) > 0
            allmin = min(minVals)
            allmax = max(maxVals)
            outList.append([allmin, allmax])
        outArr = np.array(outList)
        return outArr
    else:
        if all([len(subset) for subset in valSets]):
            mins = [min(valSet) for valSet in valSets]
            maxs = [max(valSet) for valSet in valSets]
        else:
            mins = maxs = [np.nan for valSet in valSets]
        scales = np.dstack([mins, maxs])[0]
        return scales

# def get_ranges(array, scales = None):
#     if scales is None:
#         scales = get_scales(array)
#     ranges = np.array([maxVal - minVal for minVal, maxVal in scales])
#     return ranges

class ToOpen:
    def __init__(self, filepath):
        self.filepath = filepath
    def __call__(self):
        filedata = ''
        if mpi.rank == 0:
            with open(self.filepath) as file:
                filedata = file.read()
        filedata = mpi.comm.bcast(filedata, root = 0)
        return filedata

def hash_var(var):
    underlying_datas = [
        underlying.data \
            for underlying in sorted(list(var._underlyingDataItems))
        ]
    swarms, meshes = get_substrates(var)
    substrates = [*swarms, *meshes]
    underlying_datas.extend(
        [substrate.data for substrate in substrates]
        )
    str_underlying_datas = [str(data) for data in underlying_datas]
    local_hash = hash(tuple(str_underlying_datas))
    all_hashes = mpi.comm.allgather(local_hash)
    global_hash = hash(tuple(all_hashes))
    return global_hash

def timestamp():
    stamp = time.strftime(
        '%y%m%d%H%M%SZ', time.gmtime(time.time())
        )
    return stamp
