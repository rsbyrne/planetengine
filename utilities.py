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

import planetengine
from planetengine.visualisation import quickShow
from planetengine.standards import basic_unpack

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

root = 0

def message(*args):
    for arg in args:
        if rank == 0:
            print(arg)

def log(text):
    if rank == 0:
        if os.path.isfile("diaglog.txt"):
            file = open("diaglog.txt", 'a')
        else:
            file = open("diaglog.txt", 'w')
        file.write(text)
        file.write('\n')
        file.close()

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

#     planetengine.log("Doing varsOnDisk, mode: " + mode)

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
                message("Saving substrate to disk: ", substrateName)
                handle = substrate.save(
                    os.path.join(
                        checkpointDir,
                        substrateName + extension
                        )
                    )
                substrateHandles[substrateName] = handle
            elif mode == 'load':
                message("Loading substrate from disk: ", substrateName)
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
            message("Saving var to disk: ", varName)
            var.save(os.path.join(checkpointDir, varName + extension), handle)
        elif mode == 'load':
            message("Loading var from disk: ", varName)
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
        boxDims = ((0., 1.), (0., 1.))
        ):

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

    def mapFn(tolerance):

        adjBoxDims = (
            (boxDims[0][0] + tolerance, boxDims[0][1] - tolerance),
            (boxDims[1][0] + tolerance, boxDims[1][1] - tolerance)
            )

        evalCoords = planetengine.mapping.unbox(
            inMesh,
            planetengine.mapping.box(
                outMesh,
                outCoords,
                boxDims = adjBoxDims
                )
            )

        outField.data[:] = fullInField.evaluate(evalCoords)

        message("Mapping achieved at tolerance =", tolerance)
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

    return tryTolerance

def meshify(*args):
    varName, var, mesh, swarm, coords, data, dType = \
        basic_unpack(*args)
    pemesh = planetengine.meshutils.mesh_utils(mesh)
    return pemesh.meshify(var)

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
        random.Random(shuffleseed).shuffle(listOfDicts)
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

def make_projectors(varDict):
    '''
    Takes a dictionary with keys for strings
    and values that can be either mesh variables,
    swarm variables, or tuples of the form:
    (Underworld function, substrate, dimension, dType),
    where 'substrate' is either a mesh, if the function
    is dependent solely on mesh variables, or a swarm,
    if the function is partly or wholely dependent
    on a swarm variable, and dType is a string reading either
    'double' or 'int' (the two types that Underworld functions
    can handle).
    Returns a tuple of objects which are used
    to project data structures onto mesh variables
    which are more digestible by Planetengine.
    '''
    projections = {}
    projectors = {}
    for varName, var in sorted(varDict.items()):
        if not type(var) == uw.mesh._meshvariable.MeshVariable:
            if type(var) == uw.swarm._swarmvariable.SwarmVariable:
                mesh = var.swarm.mesh
                dim = var.count
            elif type(var) == tuple:
                assert issubclass(type(var[0]), uw.function.Function), \
                    "Projections must be meshvar, swarmvar, or uw function."
                var, substrate, dim, dType = var
                try:
                    mesh = substrate.mesh
                except:
                    mesh = substrate
            projection = uw.mesh.MeshVariable(
                mesh,
                dim,
                )
            projector = uw.utils.MeshVariable_Projection(
                projection,
                var,
                )
            projections[varName] = projection
            projectors[varName] = projector
    def project(varsToProject = projectors):
        for varName in sorted(varsToProject):
            projectors[varName].solve()
    return projections, projectors, project
