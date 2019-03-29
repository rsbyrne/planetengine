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

def varsOnDisk(varsOfState, directory, mode = 'save', blackhole = [0., 0.]):
    substrates = []
    substrateNames = []
    substrateHandles = {}
    extension = '.h5'
    for var, varName in varsOfState:
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
                handle = substrate.save(os.path.join(directory, substrateName + extension))
                substrateHandles[substrateName] = handle
            elif mode == 'load':
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
            var.save(os.path.join(directory, varName + extension), handle)
        elif mode == 'load':
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
                        mesh, var = invar
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
                    swarm, var = invar
                try:
                    if not 'points' in features:
                        fig.Points(
                            swarm,
                            fn_colour = var,
                            fn_mask = var,
                            fn_size = 4.,
                            colours = "purple",
                            colourBar = False
                            )
                    else:
                        raise Exception("Got to end of swarm-based options.")
                except:
                    raise Exception("Tried everything but couldn't make it work!")

    if show:
        fig.show()
    else:
        return fig

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

def scriptstamp(scriptPath):
    with open(scriptPath, 'r') as file:
        script = file.read().encode()
    stamp = hashlib.md5(script).hexdigest()
    return stamp

def stringstamp(instring):
    stamp = hashlib.md5(instring.encode()).hexdigest()
    return stamp

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

class CoordSystems:

    class Radial:

        def __init__(
                self,
                radialLengths = (0., 1.),
                angularExtent = (0., 360.),
                boxDims = ((0., 1.), (0., 1.)),
                origin = (0., 0.),
                xFlip = True,
                ):
            # angular extents must be given in degrees
            self.radialLengths = radialLengths
            self.angularExtent = angularExtent
            self.boxDims = boxDims
            self.origin = origin

        def recentered_coords(self, coordArray):
            recenteredCoords = coordArray - self.origin
            return recenteredCoords

        def radial_coords(self, coordArray):
            recenteredCoords = self.recentered_coords(coordArray)
            xs, ys = recenteredCoords.transpose()
            angular = np.arctan2(ys, xs) * 180. / np.pi
            radial = np.hypot(xs, ys)
            radialCoords = np.dstack((angular, radial))[0]
            return radialCoords

        def curved_box(self, coordArray):
            radInScale = self.radialLengths
            angOffset = self.angularExtent[0] // 360. * 360. 
            angInScale = tuple([x - angOffset for x in self.angularExtent])
            angOutScale, radOutScale = self.boxDims
            radialCoords = self.radial_coords(coordArray)
            xs, ys = radialCoords.transpose()
            xs = np.where(xs >= 0., xs, xs + 360.)
            xs += (angOutScale[0] - angInScale[0])
            xs *= (angOutScale[1] - angOutScale[0]) / (angInScale[1] - angInScale[0])
            xs -= (angOutScale[1])
            xs *= -1.
            xs = np.clip(xs, angOutScale[0], angOutScale[1])
            ys += radOutScale[0] - radInScale[0]
            ys *= (radOutScale[1] - radOutScale[0]) / (radInScale[1] - radInScale[0])
            ys = np.clip(ys, radOutScale[0], radOutScale[1])
            curvedBox = np.dstack([xs, ys])[0]

            return curvedBox
