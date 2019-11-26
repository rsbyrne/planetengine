import numpy as np
import underworld as uw
from underworld import function as _fn
from underworld.function._function import Function as UWFn
import math
import time
import os
import itertools
import inspect
import hashlib
import random
import io

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

def check_reqs(obj):
    for attrname in obj._required_attributes:
        if not hasattr(obj, attrname):
            raise Exception(
                "Object requires attribute: '" + attrname + "'"
                )

def parallelise_set(setobj):
    setlist = []
    if mpi.rank == 0:
        setlist = list(setobj)
    setlist = mpi.comm.bcast(setlist, root = 0)
    # mpi.barrier()
    return setlist

def unpack_var(*args):

    if len(args) == 1 and type(args[0]) == tuple:
        args = args[0]
    substrate = 'notprovided'
    if len(args) == 1:
        var = args[0]
        varName = 'anon'
    elif len(args) == 2:
        if type(args[0]) == str:
            varName, var = args
        else:
            var, substrate = args
            varName = 'anon'
    elif len(args) == 3:
        varName, var, substrate = args
    else:
        raise Exception("Input not understood.")

    return var, varName, substrate

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

def check_uw(var):
    if type(var) == uw.mesh._meshvariable.MeshVariable:
        pass
    elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
        pass
    elif isinstance(var, UWFn):
        pass
    else:
        raise Exception("Not an underworld variable or function.")

def splitter(filename):
    name, ext = os.path.splitext(filename)
    while not ext == '':
        name, ext = os.path.splitext(name)
    return name

# def get_toCheck(var):
#     to_check = {}
#     # try:
#     #     to_check[var.__hash__()] = stringify(var)
#     if hasattr(var, '_underlyingDataItems'):
#         for subVar in list(var._underlyingDataItems):
#             if not subVar is var:
#                 sub_toCheck = get_toCheck(
#                     subVar
#                     )
#                 to_check.update(sub_toCheck)
#     if len(to_check) == 0:
#         if hasattr(var, 'data'):
#             to_check[var.__hash__()] = var.data
#         elif hasattr(var, 'value'):
#             to_check[var.__hash__()] = var.value
#         elif hasattr(var, 'evaluate'):
#             to_check[var.__hash__()] = var.evaluate()
#         else:
#             raise Exception
#     if hasattr(var, 'mesh'):
#         if not var.mesh is None:
#             to_check[var.mesh.__hash__()] = var.mesh.data
#     if hasattr(var, 'swarm'):
#         to_check[var.swarm.__hash__()] = var.swarm.data
#
#     return to_check

# def hash_var(
#         var,
#         global_eval = True,
#         return_checked = False,
#         **kwargs
#         ):
#     if 'checked' in kwargs:
#         checked = kwargs['checked']
#     else:
#         checked = {}
#     to_check = get_toCheck(var)
#     hashVal = 0
#     for key, val in to_check.items():
#         if key in checked:
#             hashVal += checked[key]
#         else:
#             hashVal += hash(stringify(val))
#             checked[key] = hashVal
#     assert not hashVal == 0, \
#         "Not a valid var for hashing!"
#     if global_eval:
#         hashVal = sum(mpi.comm.allgather(hashVal))
#     if return_checked:
#         return hashVal, checked
#     else:
#         return hashVal

def get_valSets(array):
    valSets = []
    assert len(array.shape) == 2
    for dimension in array.T:
        localVals = set(dimension)
        for item in list(localVals):
            if math.isnan(item):
                localVals.remove(item)
        allValsGathered = mpi.comm.allgather(localVals)
        valSet = {val.item() for localVals in allValsGathered for val in localVals}
        valSets.append(valSet)
    return valSets

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

def get_ranges(array, scales = None):
    if scales is None:
        scales = get_scales(array)
    ranges = np.array([maxVal - minVal for minVal, maxVal in scales])
    return ranges

class Grouper:
    def __init__(self, indict = {}):
        self.selfdict = {}
        self.SetDict(indict)
    def __bunch__(self, adict):
        self.__dict__.update(adict)
    def SetVal(self, key, val):
        self.selfdict[key] = val
        self.__bunch__(self.selfdict)
    def SetVals(self, dictionary):
        for key in dictionary:
            self.SetVal(key, dictionary[key])
    def ClearAttr(self):
        for key in self.selfdict:
            delattr(self, key)
        self.selfdict = {}
    def SetDict(self, dict):
        self.ClearAttr()
        self.SetVals(dict)
    def Out(self):
        outstring = ""
        for key in self.selfdict:
            thing = self.selfdict[key]
            if isinstance(thing, self):
                thing.Out()
            else:
                outstring += key + ": " + thing
        return outstring

def expose(source, destination):
    for key, value in source.__dict__.items():
        destination[key] = value

def getDefaultKwargs(function):
    argsignature = inspect.signature(function)
    argbind = argsignature.bind()
    argbind.apply_defaults()
    argdict = dict(argbind.arguments)
    return argdict

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

def stringify(*args):
    outStr = '{'
    if len(args) > 1:
        for inputObject in args:
            outStr += stringify(inputObject)
        typeStr = 'tup'
    else:
        inputObject = args[0]
        objType = type(inputObject)
        if objType == str:
            outStr += inputObject
            typeStr = 'str'
        elif objType == bool:
            outStr += str(inputObject)
            typeStr = 'boo'
        elif objType == int:
            outStr += str(inputObject)
            typeStr = 'int'
        elif objType == float:
            outStr += str(inputObject)
            typeStr = 'flt'
        elif objType in [list, tuple]:
            for item in inputObject:
                outStr += stringify(item)
            typeStr = 'tup'
        elif objType == set:
            for item in sorted(inputObject):
                outStr += stringify(item)
            typeStr = 'set'
        elif objType == dict:
            for key, val in sorted(inputObject.items()):
                outStr += (stringify(key))
                outStr += (stringify(val))
            typeStr = 'dct'
        elif objType == ToOpen:
            outStr += inputObject()
            typeStr = 'str'
        elif objType == np.ndarray:
            outStr += str(inputObject)
            typeStr = 'arr'
        else:
            errormsg = "Type: " + str(type(inputObject)) + " not accepted."
            raise Exception(errormsg)
    outStr += '}'
    # print(args)
    # print(outStr)
    outStr = typeStr + outStr
    return outStr

def hashstamp(inputObj):
    local_inputStr = stringify(inputObj)
    all_inputStrs = mpi.comm.allgather(local_inputStr)
    global_inputStr = ''.join(all_inputStrs)
    stamp = hashlib.md5(global_inputStr.encode()).hexdigest()
    return stamp

def hashToInt(inputObj):
    stamp = hashstamp(inputObj)
    random.seed(stamp)
    hashVal = random.randint(1e18, 1e19 - 1)
    random.seed()
    return hashVal

def var_check_hash(var):
    underlying_datas = [
        underlying.data \
            for underlying in sorted(list(var._underlyingDataItems))
        ]
    swarms, meshes = get_substrates(var)
    substrates = [*swarms, *meshes]
    underlying_datas.extend(
        [substrate.data for substrate in substrates]
        )
    hashVal = hashToInt(
        underlying_datas
        )
    return hashVal

def timestamp():
    stamp = time.strftime(
        '%y%m%d%H%M%SZ', time.gmtime(time.time())
        )
    return stamp
