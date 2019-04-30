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

import planetengine

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

def varsOnDisk(varsOfState, directory, mode = 'save', blackhole = [0., 0.]):
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
                if rank == 0:
                    print("Saving substrate to disk: ", substrateName)
                handle = substrate.save(os.path.join(directory, substrateName + extension))
                substrateHandles[substrateName] = handle
            elif mode == 'load':
                if rank == 0:
                    print("Loading substrate from disk: ", substrateName)
                if type(substrate) == uw.swarm.Swarm:
                    with substrate.deform_swarm():
                        substrate.particleCoordinates.data[:] = blackhole
                substrate.load(os.path.join(directory, substrateName + extension))
            else:
                raise Exception("Disk mode not recognised.")
            substrates.append(substrate)
        else:
            if mode == 'save':
                handle = substrateHandles[substrateNames]
        if mode == 'save':
            if rank == 0:
                print("Saving var to disk: ", varName)
            var.save(os.path.join(directory, varName + extension), handle)
        elif mode == 'load':
            if rank == 0:
                print("Loading var from disk: ", varName)
            var.load(os.path.join(directory, varName + extension))
        else:
            raise Exception("Disk mode not recognised.")

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

def quickShow(*args,
        show = True,
        figArgs = {
            'edgecolour': 'white',
            'facecolour': 'white',
            'quality': 2,
            }
        ):

    fig = glucifer.Figure(**figArgs)
    features = []
    for invar in args:
        try:
            if not 'mesh' in features:
                var = invar
                fig.Mesh(var)
                features.append('mesh')
            else:
                raise
        except:
            try:
                try:
                    mesh = invar.mesh
                    var = invar
                except:
                    try:
                        var, mesh = invar
                    except:
                        raise Exception("")
                try:
                    if not 'arrows' in features:
                        fig.VectorArrows(mesh, var)
                        features.append('arrows')
                    else:
                        raise
                except:
                    if not 'surface' in features:
                        fig.Surface(mesh, var)
                        features.append('surface')
                    else:
                        if not 'contours' in features:
                            fig.Contours(
                                mesh,
                                fn.math.log10(var),
                                colours = "red black",
                                interval = 0.5,
                                colourBar = False 
                                )
                            features.append('contours')
                        else:
                            raise Exception("Got to end of mesh-based options.")
            except:
                try:
                    var = invar
                    swarm = var.swarm
                except:
                    var, swarm = invar
                try:
                    if not 'points' in features:
                        fig.Points(
                            swarm,
                            fn_colour = var,
                            fn_mask = var,
                            opacity = 0.5,
                            fn_size = 1e3 / float(swarm.particleGlobalCount)**0.5,
                            colours = "purple green brown pink red",
                            colourBar = True,
                            )
                    else:
                        raise Exception("Got to end of swarm-based options.")
                except:
                    raise Exception("Tried everything but couldn't make it work!")

    if show:
        fig.show()
    else:
        return fig

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

def copyField(field1, field2,
        tolerance = 0.01,
        rounded = False
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

    assert outDim == inDim, "In and Out fields have different dimensions!"
    assert outMesh.dim == inMesh.dim, "In and Out meshes have different dimensions!"

    def mapFn(tolerance):

        evalCoords = planetengine.mapping.unbox(
            inMesh,
            planetengine.mapping.box(
                outMesh,
                outCoords,
                boxDims = outMesh.dim * ((tolerance, 1. - tolerance),)
                )
            )

        outField.data[:] = fullInField.evaluate(evalCoords)

        if rank == 0:
            print("Mapping achieved at tolerance =", tolerance)
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

def timestamp():
    stamp = time.strftime(
        '%y%m%d%H%M%SZ', time.gmtime(time.time())
        )
    return stamp

def dictstamp(inputDict):
    inputStr = str(
        [(key, inputDict[key]) for key in sorted(inputDict)]
        ).encode()
    stamp = hashlib.md5(inputStr).hexdigest()
    return stamp

def multidictstamp(dictList):
    inputBytes = bytes()
    for inputDict in dictList:
        inputBytes += str(
        [(key, inputDict[key]) for key in sorted(inputDict)]
        ).encode()
    stamp = hashlib.md5(inputBytes).hexdigest()
    return stamp

def scriptstamp(scriptPath):
    with open(scriptPath, 'r') as file:
        script = file.read().encode()
    stamp = hashlib.md5(script).hexdigest()
    return stamp

def multiscriptstamp(scriptList):
    script = bytes()
    for scriptPath in scriptList:
        with open(scriptPath, 'r') as file:
            script += file.read().encode()
    stamp = hashlib.md5(script).hexdigest()
    return stamp

def stringstamp(instring):
    stamp = hashlib.md5(instring.encode()).hexdigest()
    return stamp

def mesh_utils(mesh, deformable = False):

    try:
        meshName, mesh = mesh
    except:
        mesh = mesh
        meshName = 'None'

    if hasattr(mesh, 'pe'):
        if rank == 0:
            print("Mesh already has 'pe' attribute: aborting.")
        return None

    pe = {
        'deformable': deformable,
        'meshName': meshName,
        }

    if type(mesh) == uw.mesh.FeMesh_Cartesian:
        if mesh.dim == 2:
            pe['ang'] = fn.misc.constant((1., 0.))
            pe['rad'] = fn.misc.constant((0., 1.))
        elif mesh.dim == 3:
            pe['ang1'] = fn.misc.constant((1., 0., 0.))
            pe['ang2'] = fn.misc.constant((0., 1., 0.))
            pe['rad'] = fn.misc.constant((0., 0., 1.))
        else:
            raise Exception("Only mesh dims 2 and 3 supported...obviously?")
        pe['inner'] = mesh.specialSets['Bottom']
        pe['outer'] = mesh.specialSets['Top']
    elif type(mesh) == uw.mesh.FeMesh_Annulus:
        pe['ang'] = mesh.unitvec_theta_Fn
        pe['rad'] = mesh.unitvec_r_Fn
        pe['inner'] = mesh.specialSets['inner']
        pe['outer'] = mesh.specialSets['outer']
    else:
        raise Exception("That kind of mesh is not supported yet.")

    if mesh.dim == 2:
        pe['comps'] = {
            'ang': pe['ang'],
            'rad': pe['rad'],
            }
    else:
        pe['comps'] = {
            'ang1': pe['ang1'],
            'ang2': pe['ang2'],
            'rad': pe['rad'],
            }

    pe['surfaces'] = {
        'inner': pe['inner'],
        'outer': pe['outer'],
        }

    def getFullData():
        fullData = fn.input().evaluate_global(mesh.data)
        fullData = comm.bcast(fullData, root = 0)
        return fullData

    # Is this necessary?
    if not deformable:
        fullData = getFullData()
        pe['fullData'] = lambda: fullData
    else:
        pe['fullData'] = getFullData

    # REVISIT THIS WHEN 'BOX' IS IMPROVED
    if type(mesh) == uw.mesh.FeMesh_Annulus:
        if not deformable:
            if mesh.dim == 2:
                box = planetengine.mapping.box(mesh)
                pe['box'] = lambda: box
        else:
            if mesh.dim == 2:
                pe['box'] = lambda: mapping.box(mesh)

    volInt = uw.utils.Integral(
        1.,
        mesh,
        )
    outerInt = uw.utils.Integral(
        1.,
        mesh,
        integrationType = 'surface',
        surfaceIndexSet = pe['outer']
        )
    innerInt = uw.utils.Integral(
        1.,
        mesh,
        integrationType = 'surface',
        surfaceIndexSet = pe['inner']
        )

    if not deformable:

        volIntVal = volInt.evaluate()[0]
        outerIntVal = outerInt.evaluate()[0]
        innerIntVal = innerInt.evaluate()[0]

        pe['integral'] = lambda: volIntVal
        pe['integral_outer'] = lambda: outerIntVal
        pe['integral_inner'] = lambda: innerIntVal

    else:

        pe['integral'] = lambda: volInt.evaluate()[0]
        pe['integral_outer'] = lambda: outerInt.evaluate()[0]
        pe['integral_inner'] = lambda: innerInt.evaluate()[0]

    pe['integrals'] = {
        'inner': pe['integral_inner'],
        'outer': pe['integral_outer'],
        'volume': pe['integral'],
        }

    pe = Grouper(pe)
    mesh.__dict__.update({'pe': pe})

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

def setboundaries(variable, values):
    try:
        mesh = variable.mesh
    except:
        raise Exception("Variable does not appear to be mesh variable.")
    walls = [
        mesh.specialSets["outer"],
        mesh.specialSets["inner"],
        mesh.specialSets["MinJ_VertexSet"],
        mesh.specialSets["MaxJ_VertexSet"],
        ]
    for value, wall in zip(values, walls):
        if not value is '.':
            variable.data[wall] = value

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
