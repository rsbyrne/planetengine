import numpy as np
import underworld as uw
from underworld import function as fn
import glucifer
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
import hashlib
import random
import io

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

from . import standards
from .standards import standardise
from . import mapping

root = 0

def message(*args):
    for arg in args:
        if rank == 0:
            print(arg)

def log(text, outputPath = '', outputName = 'diaglog.txt'):
    if rank == 0:
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

def hash_var(var):
    hashVal = 0
    if hasattr(var, 'value'):
        hashVal += hash(str(var.value))
    if hasattr(var, 'data'):
        hashVal += hash(str(var.data))
    if hasattr(var, 'mesh'):
        hashVal += hash_var(var.mesh)
    if hasattr(var, 'swarm'):
        hashVal += hash_var(var.swarm)
    if hasattr(var, '_underlyingDataItems'):
        for subVar in var._underlyingDataItems:
            if not var is subVar:
                hashVal += hash_var(subVar)
    assert not hashVal == 0, \
        "Not a valid var for hashing!"
    global_hashVal = sum(comm.allgather(hashVal))
    return global_hashVal

def get_valSet(var):
    try:
        data = var.data
    except:
        data = var
    localVals = {val for row in data for val in row}
    allValsGathered = comm.allgather(localVals)
    valSet = {val for localVals in allValsGathered for val in localVals}
    return valSet

def get_scales(variable):
    try:
        array = variable.data
    except:
        array = variable
    dims = array.shape[1]
    localMins = [np.min(array[:, dim]) for dim in range(dims)]
    allMins = comm.allgather(localMins)
    globalMins = np.min(allMins, axis = 0)
    localMaxs = [np.max(array[:, dim]) for dim in range(dims)]
    allMaxs = comm.allgather(localMaxs)
    globalMaxs = np.max(allMaxs, axis = 0)
    scales = np.dstack([globalMins, globalMaxs])[0]
    return scales

def get_ranges(variable):
    scales = get_scales(variable)
    ranges = [maxVal - minVal for minVal, maxVal in scales]
    return ranges

def set_boundaries(variable, values):

    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")

    walls = standardise(mesh).wallsList

    for i, component in enumerate(values):
        for value, wall in zip(component, walls):
            if not value is '.':
                variable.data[wall, i] = value

def set_scales(variable, values):

    variable.data[:] = mapping.rescale_array(
        variable.data,
        get_scales(variable),
        values
        )

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

def unpack_var(*args, return_dict = False):

    if len(args) == 1 and type(args[0]) == tuple:
        args = args[0]
    substrate = None
    if len(args) == 1:
        var = args[0]
    elif len(args) == 2:
        if type(args[0]) == str:
            varName, var = args
        else:
            var, substrate = args
    elif len(args) == 3:
        varName, var, substrate = args
    else:
        raise Exception("Input not understood.")

    if substrate is None:
        try:
            substrate = var.swarm
        except:
            try:
                substrate = var.mesh
            except:
                subVars = []
                for subVar in var._underlyingDataItems:
                    try: subVars.append(unpack_var(subVar))
                    except: pass
                if len(subVars) == 0:
                    message(
                        "No substrate detected or was provided: \
                        using default mesh."
                        )
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

    if substrate is None:
        try:
            substrate = standards.default_mesh[2]
            data = var.evaluate(substrate)
        except:
            substrate = standards.default_mesh[3]
            data = var.evaluate(substrate)
    else:
        data = var.evaluate(substrate)

    varDim = data.shape[1]

    try:
        mesh = substrate.mesh
    except:
        mesh = substrate

    if type(var) == uw.swarm._swarmvariable.SwarmVariable:
        varType = 'swarmVar'
    elif type(var) == uw.mesh._meshvariable.MeshVariable:
        varType = 'meshVar'
    else:
        if hasattr(substrate, 'particleCoordinates'):
            varType = 'swarmFn'
        else:
            varType = 'meshFn'

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

    if return_dict:
        outDict = {
            'var': var,
            'varType': varType,
            'mesh': mesh,
            'substrate': substrate,
            'dType': dType,
            'varDim': varDim
            }
        return outDict
    else:
        return var, varType, mesh, substrate, dType, varDim

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

#     planetengine.log("Finished doing varsOnDisk, mode: " + mode)

def weightVar(mesh, specialSets = None):

    maskVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)
    weightVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)

    if specialSets == None:
        localIntegral = uw.utils.Integral(maskVar, mesh)
    else:
        localIntegral = uw.utils.Integral(
            maskVar,
            mesh,
            integrationType = 'surface',
            surfaceIndexSet = specialSets
            )

    for index, val in enumerate(weightVar.data):
        maskVar.data[:] = 0.
        maskVar.data[index] = 1.
        weightVar.data[index] = localIntegral.evaluate()[0]
    return weightVar

def makeLocalAnnulus(mesh):
    for proc in range(nProcs):
        if rank == proc:
            localAnn = uw.mesh.FeMesh_Annulus(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                radialLengths = mesh.radialLengths,
                angularExtent = mesh.angularExtent,
                periodic = mesh.periodic,
                partitioned = False,
                )
    return localAnn

def makeLocalCart(mesh):
    for proc in range(nProcs):
        if rank == proc:
            localMesh = uw.mesh.FeMesh_Cartesian(
                elementType = mesh.elementType,
                elementRes = mesh.elementRes,
                minCoord = mesh.minCoord,
                maxCoord = mesh.maxCoord,
                periodic = mesh.periodic,
                partitioned = False,
                )
    return localMesh

def copyField(field1, field2,
        tolerance = 0.01,
        rounded = False,
        boxDims = None,
        freqs = None,
        mirrored = None,
        blendweight = None,
        scales = None,
        boundaries = None,
        ):

    if not boxDims is None:
        assert np.max(np.array(boxDims)) <= 1., "Max boxdim is 1."
        assert np.min(np.array(boxDims)) >= 0., "Min boxdim is 0."

    if type(field1) == uw.mesh._meshvariable.MeshVariable:
        inField = field1
        inMesh = field1.mesh
        inDim = field1.nodeDofCount
    else:
        inMesh = field1.swarm.mesh
        field1Proj = uw.mesh.MeshVariable(
            inMesh,
            field1.count,
            )
        field1Projector = uw.utils.MeshVariable_Projection(
            field1Proj,
            field1
            )
        field1Projector.solve()
        inField = field1Proj
        inDim = field1.count

    fullInField = makeLocalAnnulus(inMesh).add_variable(inDim)
    allData = comm.gather(inField.data, root = 0)
    allGID = comm.gather(inField.mesh.data_nodegId, root = 0)
    idDict = {}
    if rank == 0:
        for proc in range(nProcs):
            for data, ID in zip(allData[proc], allGID[proc]):
                fullInField.data[ID] = data
    fullInField.data[:] = comm.bcast(fullInField.data, root = 0)

    outField = field2
    if type(field2) == uw.mesh._meshvariable.MeshVariable:
        outMesh = field2.mesh
        outCoords = outMesh.data
        outDim = field2.nodeDofCount
    else:
        outMesh = field2.swarm.mesh
        outCoords = field2.swarm.particleCoordinates.data
        outDim = field2.count

    assert outDim == inDim, \
        "In and Out fields have different dimensions!"
    assert outMesh.dim == inMesh.dim, \
        "In and Out meshes have different dimensions!"

    outBox = mapping.box(
        outMesh,
        outCoords,
        boxDims,
        freqs,
        mirrored
        )

    def mapFn(tolerance):

        evalCoords = mapping.unbox(
            inMesh,
            outBox,
            tolerance = tolerance
            )

        newData = fullInField.evaluate(evalCoords)
        oldData = outField.data[:]
        if not blendweight is None:
            newData = np.sum(
                np.array([oldData, blendweight * newData]),
                axis = 0
                ) \
                / (blendweight + 1)

        outField.data[:] = newData

        message("Mapping achieved at tolerance = " + str(tolerance))
        return tolerance

    tryTolerance = 0.

    while True:
        try:
            tryTolerance = mapFn(tryTolerance)
            break
        except:
            if tryTolerance > 0.:
                tryTolerance *= 1.01
            else:
                tryTolerance += 0.00001
            if tryTolerance > tolerance:
                raise Exception("Couldn't find acceptable tolerance.")
            else:
                pass

    if rounded:
        field2.data[:] = np.around(field2.data)

#     inPemesh = planetengine.standards.make_pemesh(inMesh)
#     outPemesh = planetengine.standards.make_pemesh(outMesh)
#     for inWall, outWall in zip(inPemesh.wallsList, outPemesh.wallsList):
#         planetengine.mapping.boundary_interpolate(
#             (inField, inMesh, inWall),
#             (outField, outMesh, outWall),
#             inDim
#             )

    if not scales is None:
        set_scales(field2, scales)

    if not boundaries is None:
        set_boundaries(field2, boundaries)

    return tryTolerance

def meshify(*args, return_project = False):
    var, varType, mesh, substrate, dType, varDim = \
        unpack_var(*args)
    pemesh = standardise(mesh)
    rounded = dType in ('int', 'boolean')
    meshVar = pemesh.meshify(
        var,
        return_project = return_project,
        rounded = rounded
        )
    return meshVar

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
    outStr = '('
    if len(args) > 1:
        for inputObject in args:
            outStr += stringify(inputObject)
    else:
        inputObject = args[0]
        objType = type(inputObject)
        if objType == str:
            outStr += inputObject
        elif objType == bool:
            outStr += str(inputObject)
        elif objType == int:
            outStr += str(float(inputObject))
        elif objType == float:
            outStr += str(inputObject)
        elif objType in [list, tuple]:
            for item in inputObject:
                outStr += stringify(item)
        elif objType == set:
            for item in sorted(inputObject):
                outStr += stringify(item)
        elif objType == dict:
            for key, val in sorted(inputObject.items()):
                outStr += (stringify(key))
                outStr += (stringify(val))
        elif objType == io.TextIOWrapper:
            file = inputObject.read()
            outStr += file
            inputObject.close()
        else:
            errormsg = "Type: " + str(type(inputObject)) + " not accepted."
            raise Exception(errormsg)
    outStr += ')'
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

def make_projector(*args):

    var, varType, mesh, substrate, dType, varDim = unpack_var(args)
    projection = uw.mesh.MeshVariable(
        mesh,
        varDim,
        )
    projector = uw.utils.MeshVariable_Projection(
        projection,
        var,
        )

    inherited_proj = []
    for subVar in var._underlyingDataItems:
        try: inherited_proj.append(subVar.project)
        except: pass

    setattr(projection, 'lasthash', 0)

    def project():
        currenthash = hash_var(var)
        if projection.lasthash == currenthash:
            message(
                "No underlying change detected: \
                skipping projection."
                )
            pass
        else:
            for inheritedProj in inherited_proj:
                inheritedProj()
            projector.solve()
            if dType in ('int', 'boolean'):
                projection.data[:] = np.round(
                    projection.data
                    )
            projection.lasthash = currenthash

    setattr(projection, 'projector', projector)
    setattr(projection, 'project', project)
    setattr(projection, 'inherited_proj', inherited_proj)

    return projection