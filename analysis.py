
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

import planetengine

class Analyse:

    class asdfDimensionlessGradient:

        def __init__(self, scalarField, mesh,
                     component = 1,
                     baseSet = None,
                     surfSet = None
                    ):

            self.intSurfGrad = uw.utils.Integral(
                scalarField.fn_gradient[component], mesh,
                integrationType = 'surface',
                surfaceIndexSet = surfSet
                )
            self.intBase = uw.utils.Integral(
                scalarField, mesh,
                integrationType = 'surface',
                surfaceIndexSet = baseSet
                )

        def evaluate(self):

            Nu = - self.intSurfGrad.evaluate()[0] \
                / self.intBase.evaluate()[0]
            return Nu

    class DimensionlessGradient:

        def __init__(self, scalarField, mesh,
                     component = 1,
                     surfIndexSet = None,
                     baseIndexSet = None
                    ):

            self.intSurfGrad = uw.utils.Integral(
                scalarField.fn_gradient[component], mesh,
                integrationType = 'surface',
                surfaceIndexSet = surfIndexSet
                )
            self.intBase = uw.utils.Integral(
                scalarField, mesh,
                integrationType = 'surface',
                surfaceIndexSet = baseIndexSet
                )

        def evaluate(self):

            Nu = - self.intSurfGrad.evaluate()[0] \
                / self.intBase.evaluate()[0]
            return Nu

    class ScalarFieldAverage:

        def __init__(self, field, mesh):

            self.intField = uw.utils.Integral(field, mesh)
            self.intMesh = uw.utils.Integral(1., mesh)

        def evaluate(self):

            average = self.intField.evaluate()[0] \
                / self.intMesh.evaluate()[0]
            return average

    class VectorFieldVolRMS:

        def __init__(self, vectorField, mesh):

            self.intVdotV = uw.utils.Integral(
                fn.math.dot(vectorField, vectorField), mesh)
            self.intMesh = uw.utils.Integral(1., mesh)

        def evaluate(self):

            fieldrms = math.sqrt(self.intVdotV.evaluate()[0]) \
                / self.intMesh.evaluate()[0]
            return fieldrms

    class VectorFieldSurfRMS:

        def __init__(self, vectorField, mesh, indexSet):

            self.intVdotV = uw.utils.Integral(
                fn.math.dot(vectorField, vectorField), mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
            self.intMesh = uw.utils.Integral(
                1., mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet          
                )

        def evaluate(self):

            fieldrms = math.sqrt(self.intVdotV.evaluate()[0]) \
                / self.intMesh.evaluate()[0]
            return fieldrms

    class Constant:

        def __init__(self, constant):

            self.constant = constant

        def evaluate(self):

            return self.constant

    class ArrayStripper:

        def __init__(self, arrayobj, indexer):
            # input should be a numpy array
            # and an appropriate tuple of indices
            # to index the target value.

            self.array = arrayobj
            self.indexer = indexer

        def evaluate(self):

            value = self.array.evaluate()
            for index in self.indexer:
                value = value[index]
            return value

class Analyser:

    def __init__(self, name, analyserDict, formatDict):

        self.analyserDict = analyserDict
        self.formatDict = formatDict
        self.header = sorted(analyserDict, key=str.lower)
        self.headerStr = ', '.join(self.header)
        self.dataDict = {}
        self.data = [None] * len(self.header)
        self.name = name
        self.dataBrief = "No data."

    def analyse(self):

        for key in self.analyserDict:
            self.dataDict[key] = self.analyserDict[key].evaluate()
        self.data = [self.dataDict[key] for key in self.header]
        self.keys = sorted(self.dataDict, key = str.lower)
        self.dataBrief = [(key, self.formatDict[key].format(self.dataDict[key])) for key in self.keys]

    def report(self):

        if uw.rank() == 0:
            for pair in self.dataBrief:
                print(pair[0], pair[1])

class DataCollector:

    def __init__(self, analysers):

        self.analysers = analysers
        self.headers = [analyser.headerStr for analyser in self.analysers]
        self.names = [analyser.name for analyser in self.analysers]
        self.datasets = [[] for analyser in self.analysers]

    def collect(self, refresh = False):

        for index, analyser in enumerate(self.analysers):
            if refresh:
                analyser.analyse()
            self.datasets[index].append(analyser.data)

    def clear(self):

        outdata = []
        for name, headerStr, dataset in zip(self.names, self.headers, self.datasets):
            if len(dataset) > 0:
                dataArray = np.vstack(dataset)
            else:
                dataArray = None
            outdata.append((name, headerStr, dataArray))
        self.datasets = [[] for analyser in self.analysers]
        return outdata
