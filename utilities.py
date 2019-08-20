import numpy as np
import underworld as uw
from underworld import function as fn
from underworld.function._function import Function as UWFn
import math
import time
import os
import itertools
import inspect
import importlib
import hashlib
import random
import io

def message(*args):
    for arg in args:
        if uw.mpi.rank == 0:
            print(arg)

def log(text, outputPath = '', outputName = 'diaglog.txt'):
    if uw.mpi.rank == 0:
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

def get_substrate(var):
    try:
        substrate = var.swarm
    except:
        try:
            substrate = var.mesh
        except:
            subVars = []
            for subVar in var._underlyingDataItems:
                try: subVars.append(get_varInfo(subVar, return_var = True))
                except: pass
            if len(subVars) == 0:
                substrate = None
            else:
                subSwarms = list(set([
                    subVar[3] for subVar in subVars \
                        if subVar[1] in ('swarmVar', 'swarmFn')
                    ]))
                if len(subSwarms) > 0:
                    assert len(subSwarms) < 2, \
                        "Multiple swarm dependencies detected: \
                        try providing a substrate manually."
                    substrate = subSwarms[0]
                else:
                    subMeshes = list(set([
                        subVar[3] for subVar in subVars \
                            if subVar[1] in ('meshVar', 'meshFn')
                        ]))
                    for a, b in itertools.combinations(subMeshes, 2):
                        if a is b.subMesh:
                            subMeshes.pop(a)
                        elif b is a.subMesh:
                            subMeshes.pop(b)
                    assert len(subMeshes) < 2, \
                        "Multiple mesh dependencies detected: \
                        try providing a substrate manually."
                    substrate = subMeshes[0]
    return substrate

def get_mesh(var):
    substrate = get_substrate(var)
    try:
        mesh = substrate.mesh
    except:
        mesh = substrate
    return mesh

def get_substrates(var):
    substrate = get_substrate(var)
    try:
        mesh = substrate.mesh
    except:
        mesh = substrate
    return mesh, substrate

def get_varInfo(*args, detailed = False, return_var = False):

    var, varName, substrate = unpack_var(*args)

    var = UWFn.convert(var)
    if var is None:
        raise Exception

    if substrate == 'notprovided':
        substrate = get_substrate(var)

    data = var.evaluate(substrate)

    varDim = data.shape[1]

    try:
        mesh = substrate.mesh
    except:
        mesh = substrate

    if type(var) == fn.misc.constant:
        varType = 'constant'
    elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
        varType = 'swarmVar'
    elif type(var) == uw.mesh._meshvariable.MeshVariable:
        varType = 'meshVar'
    else:
        if substrate is mesh:
            varType = 'meshFn'
        else:
            varType = 'swarmFn'

    if str(data.dtype) == 'int32':
        dType = 'int'
    elif str(data.dtype) == 'float64':
        dType = 'double'
    elif str(data.dtype) == 'bool':
        dType = 'boolean'
    else:
        raise Exception(
            "Input data type not acceptable."
            )

    if detailed:
        outDict = {
            'varType': varType,
            'mesh': mesh,
            'substrate': substrate,
            'dType': dType,
            'varDim': varDim,
            'varName': varName,
            }
        if return_var:
            return var, outDict
        else:
            return outDict
    else:
        if return_var:
            return var, varType, mesh, substrate, dType, varDim
        else:
            return varType, mesh, substrate, dType, varDim

def splitter(filename):
    name, ext = os.path.splitext(filename)
    while not ext == '':
        name, ext = os.path.splitext(name)
    return name

def get_toCheck(var, checked = {}):
    to_check = {}
    try:
        to_check[var] = stringify(var)
    except:
        if hasattr(var, 'mesh'):
            to_check[var.mesh] = var.mesh.data
        if hasattr(var, 'swarm'):
            to_check[var.swarm] = var.swarm.data
        if hasattr(var, 'data'):
            to_check[var] = var.data
        if hasattr(var, '_underlyingDataItems'):
            for subVar in list(var._underlyingDataItems):
                if not subVar is var:
                    sub_toCheck = get_toCheck(
                        subVar,
                        checked
                        )
                    to_check.update(sub_toCheck)
    return to_check

def hash_var(
        var,
        checked = {},
        global_eval = True,
        return_checked = False
        ):
    to_check = get_toCheck(var, checked)
    hashVal = 0
    for key, val in to_check.items():
        if key in checked:
            hashVal += checked[key]
        else:
            hashVal += hash(stringify(val))
            checked[key] = hashVal
    assert not hashVal == 0, \
        "Not a valid var for hashing!"
    if global_eval:
        hashVal = sum(uw.mpi.comm.allgather(hashVal))
    if return_checked:
        return hashVal, checked
    else:
        return hashVal

    # hashVal = 0
    # checked = [var]
    # print(type(var))
    # def hash_obj(obj):
    #     if not obj in checked:
    #         addVal, _checked = hash_var(
    #             obj,
    #             _check_redundancy = True
    #             )
    #         hashVal += addVal
    #         checked.append(_checked)
    # if type(var) == tuple:
    #     for subVar in var:
    #         hash_obj(subVar)
    # if hasattr(var, 'value'):
    #     hashVal += hash(str(var.value))
    # if hasattr(var, 'data'):
    #     hashVal += hash(str(var.data))
    # if hasattr(var, 'mesh'):
    #     hashVal += hash_var(var.mesh)
    #     hash_obj(var.mesh)
    # if hasattr(var, 'swarm'):
    #     hashVal += hash_var(var.swarm)
    #     hash_obj(var.swarm)
    # if hasattr(var, '_underlyingDataItems'):
    #     for subVar in var._underlyingDataItems:
    #         if not var is subVar:
    #             hashVal += hash_var(subVar)
    #             hash_obj(subVar)
    # assert not hashVal == 0, \
    #     "Not a valid var for hashing!"
    # global_hashVal = sum(uw.mpi.comm.allgather(hashVal))
    # if _check_redundancy:
    #     return global_hashVal, checked
    # else:
    #     return global_hashVal

def get_valSets(array):
    valSets = []
    for dimension in array.T:
        localVals = set(dimension)
        for item in list(localVals):
            if math.isnan(item):
                localVals.remove(item)
        allValsGathered = uw.mpi.comm.allgather(localVals)
        valSet = {val for localVals in allValsGathered for val in localVals}
        valSets.append(valSet)
    return valSets

def get_scales(array, valSets = None):
    if valSets is None:
        valSets = get_valSets(array)
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

def varsOnDisk(varsOfState, checkpointDir, mode = 'save', blackhole = [0., 0.]):
    substrates = []
    substrateNames = []
    substrateHandles = {}
    extension = '.h5'

    for varName, var in sorted(varsOfState.items()):

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
                substrateHandles[substrateName] = handle
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
                handle = substrateHandles[substrateNames]

        if mode == 'save':
            message("Saving var to disk: " + varName)
            var.save(os.path.join(checkpointDir, varName + extension), handle)
        elif mode == 'load':
            message("Loading var from disk: " + varName)
            var.load(os.path.join(checkpointDir, varName + extension))
        else:
            raise Exception("Disk mode not recognised.")

def expose(source, destination):
    for key, value in source.__dict__.items():
        destination[key] = value

def suite_list(listDict, shuffle = False, chunks = None, shuffleseed = 1066):
    listOfKeys = sorted(listDict)
    listOfVals = []
    listOfDicts = []
    for key in listOfKeys:
        val = listDict[key]
        if type(val) == list:
            entry = val
        else:
            entry = [val]
        listOfVals.append(entry)
    combinations = list(itertools.product(*listOfVals))
    for item in combinations:
        newDict = {key: val for key, val in zip(listOfKeys, item)}
        listOfDicts.append(newDict)
    if shuffle:
        random.seed(shuffleseed)
        random.shuffle(listOfDicts)
        random.seed()
    if chunks == None:
        outList = listOfDicts
    elif chunks > 0:
        outList = split_list(listOfDicts, chunks)
    else:
        outList = [[thing] for thing in listOfDicts]
    return outList

def split_list(a, n):
    k, m = divmod(len(a), n)
    return list(
        (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))
        )

def getDefaultKwargs(function):
    argsignature = inspect.signature(function)
    argbind = argsignature.bind()
    argbind.apply_defaults()
    argdict = dict(argbind.arguments)
    return argdict

def local_import(filepath):

    modname = os.path.basename(filepath)

    spec = importlib.util.spec_from_file_location(
        modname,
        filepath,
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def stringify(*args):
    outStr = '{'
    if len(args) > 1:
        for inputObject in args:
            outStr += stringify(inputObject)
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
        elif objType == io.TextIOWrapper:
            file = inputObject.read()
            outStr += file
            inputObject.close()
            typeStr = 'str'
        elif objType == np.ndarray:
            outStr += str(inputObject)
            typeStr = 'arr'
        else:
            errormsg = "Type: " + str(type(inputObject)) + " not accepted."
            raise Exception(errormsg)
    outStr += '}'
    outStr = typeStr + outStr
    return outStr

def hashstamp(inputObj):
    inputStr = stringify(inputObj).encode()
    stamp = hashlib.md5(inputStr).hexdigest()
    return stamp

def timestamp():
    stamp = time.strftime(
        '%y%m%d%H%M%SZ', time.gmtime(time.time())
        )
    return stamp
