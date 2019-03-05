
# coding: utf-8

# In[1]:


import numpy as np
import underworld as uw
from underworld import function as fn
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

class Group():

    def __init__(self, listofICs):
        self.listofICs = listofICs

    def apply(self):
        for condition in self.listofICs:
            condition.apply()

class NoisyGradient:

    def __init__(
            self,
            variableArray,
            coordArray,
            gradient = 1.,
            exponent = 1.,
            smoothness = 1,
            randomSeed = 1066,
            tempRange = (0., 1.),
            ):

        self.variableArray = variableArray

        tempMin, tempMax = tempRange
        deltaT = tempRange[1] - tempRange[0]
        depthArray = 1. - coordArray[:,1]
        outArray = (depthArray * gradient) ** exponent
        np.random.seed(randomSeed)
        randomArray = (np.random.rand(outArray.shape[0]) * 2. - 1.) / smoothness
        outArray = outArray + randomArray
        outArray = (outArray + tempMin) * deltaT
        outArray = np.clip(outArray, tempMin, tempMax)
        outArray = np.vstack(outArray)

        self.outArray = outArray

    def apply(self):
        self.variableArray[:] = self.outArray

class LoadField:

    def __init__(
            self,
            field = None,
            filename = None,
            inputDim = 1,
            inputRes = (64, 64),
            inputCoords = ((0., 0.), (1., 1.)),
            mapper = None,
            ):
        self.field = field
        for proc in range(uw.nProcs()):
            if uw.rank() == proc:
                inputMesh = uw.mesh.FeMesh_Cartesian(
                    elementRes = inputRes,
                    minCoord = inputCoords[0],
                    maxCoord = inputCoords[1],
                    partitioned = False
                    )
                inField = inputMesh.add_variable(inputDim)
                inField.load(filename)
        if type(mapper) == type(None):
            mapper = self.field.mesh
        self.newData = inField.evaluate(mapper)

    def apply(self):
        self.field.data[:] = self.newData

class Sinusoidal:

    def __init__(
            self, variableArray, coordArray,
            pert = 0.2,
            freq = 1.,
            tempRange = (0., 1.),
            phase = 0.,
            boxDims = (1., 1.), # length, height
            ):
        self.variableArray = variableArray
        self.coordArray = coordArray
        self.freq = freq
        self.tempRange = tempRange
        self.phase = phase
        self.pert = pert
        self.boxDims = boxDims

    def sinusoidal_IC(self):
        boxLength, boxHeight = self.boxDims
        tempMin, tempMax = self.tempRange
        deltaT = self.tempRange[1] - self.tempRange[0]
        pertArray = \
            self.pert \
            * np.cos(np.pi * (self.phase + self.freq * self.coordArray[:,0])) \
            * np.sin(np.pi * self.coordArray[:,1])
        outArray = tempMin + deltaT * (boxHeight - self.coordArray[:,1]) + pertArray
        outArray = np.clip(outArray, tempMin, tempMax)
        outArray = np.array([[item] for item in outArray])
        return outArray

    def apply(self):
        self.variableArray[:] = self.sinusoidal_IC()

class Extents:

    def __init__(self, variableArray, coordArray, initialExtents):
        self.variableArray = variableArray
        self.coordArray = coordArray
        self.initialExtents = initialExtents

    def initial_extents(self):
        ICarray = np.zeros(np.shape(self.variableArray), dtype=np.int)
        for val, polygonFn in self.initialExtents:
            ICarray = np.where(
                polygonFn.evaluate(self.coordArray),
                [val],
                ICarray
                )
        return ICarray

    def apply(self):
        self.variableArray[:] = self.initial_extents()
        

class Indices:

    def __init__(self, variableArray, indexControls, boundaries = None):
        self.variableArray = variableArray
        self.indexControls = indexControls

    def apply(self):
        for indices, val in self.indexControls:
            self.variableArray[indices] = val

class SetVal:

    def __init__(self, invar, val):
        if type(invar) is list:
            self.variableList = invar
        else:
            self.variableList = [invar,]
        self.val = val

    def apply(self):
        valType = type(self.val)
        for variable in self.variableList:
            varType = type(variable)
            if valType is np.ndarray:
                if varType is np.ndarray:
                    variable[:] = self.val[:]
                elif varType is float or varType is int:
                    variable = self.val[:]
                else:
                    raise Exception("Input to 'setval' not recognised: only np arrays, ints, or floats accepted.")
            elif valType is float or valType is int:
                if varType is np.ndarray:
                    variable[:] = self.val
                elif varType is float or varType is int:
                    variable = self.val
                else:
                    raise Exception("Input to 'setval' not recognised: only np arrays, ints, or floats accepted.")
            else:
                raise Exception("Input to 'setval' not recognised: only np arrays, ints, or floats accepted.")