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

import planetengine

def weightVar(mesh, specialSets = None):

    maskVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)
    weightVar = uw.mesh.MeshVariable(mesh, nodeDofCount = 1)

    if specialSets = None:
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

def quickShow(var):
    fig = glucifer.Figure(edgecolour = 'white')
    try:
        fig.append(glucifer.objects.Mesh(var))
    except:
        mesh = var.mesh
        fig.append(glucifer.objects.Surface(mesh, var))
    fig.show()

def suite_list(listDict):
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
    return listOfDicts

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
    stamp = "_" + time.strftime(
        '%y%m%d%H%M%SZ', time.gmtime(time.time())
        )
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
            xs = np.clip(xs, angOutScale[0], angOutScale[1])
            ys += radOutScale[0] - radInScale[0]
            ys *= (radOutScale[1] - radOutScale[0]) / (radInScale[1] - radInScale[0])
            ys = np.clip(ys, radOutScale[0], radOutScale[1])
            curvedBox = np.dstack([xs, ys])[0]

            return curvedBox
