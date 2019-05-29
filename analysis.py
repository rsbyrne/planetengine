
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

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

import planetengine

class ScalarIntegral:

    def __init__(
            self,
            field,
            mesh,
            gradient = None,
            surface = None,
            nonDim = None,
            ):

        if gradient is None:
            var = field
        else:
            grad = field.fn_gradient
            if gradient == 'natural':
                var = grad
            else:
                if gradient == 'radial':
                    comp = -mesh.unitvec_r_Fn
                elif gradient == 'angular':
                    comp = mesh.unitvec_theta_Fn
                else:
                    raise Exception(
                        "Gradient input not recognised."
                        )
                var = fn.math.dot(comp, grad)

        if surface == None:
            intField = uw.utils.Integral(field, mesh)
            intMesh = uw.utils.Integral(1., mesh)
        else:
            indexSet = mesh.specialSets[surface]
            intField = uw.utils.Integral(
                field,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
            intMesh = uw.utils.Integral(
                1.,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )

        val = lambda: \
            intField.evaluate()[0] \
            / intMesh.evaluate()[0]

        if nonDim is None:
            ndVal = lambda: 1.
        else:
            ndVal = lambda: nonDim.evaluate()

        self.evaluate = lambda: val() / ndVal

    def __call__(self):

        return self.evaluate()

class Analyse:

    class DimensionlessGradient:

        def __init__(self, scalarField, mesh, surface, nonDim = 'inner'):

            intFieldSurfGrad = uw.utils.Integral(
                fn.math.dot(mesh.unitvec_r_Fn, scalarField.fn_gradient),
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = surface
                )

            intMeshSurf = uw.utils.Integral(
                1.,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = surface
                )

            self.val = lambda: \
                -intFieldSurfGrad.evaluate()[0] \
                / intMeshSurf.evaluate()[0]

            if type(nonDim) == int or type(nonDim) == float:

                self.nonDimVal = lambda: float(nonDim)

            elif type(nonDim) == uw.mesh._mesh.FeMesh_IndexSet:

                intMeshNd = uw.utils.Integral(
                    1.,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                intFieldNd = uw.utils.Integral(
                    scalarField,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                self.nonDimVal = lambda: \
                    intMeshNd.evaluate()[0] \
                    / intFieldNd.evaluate()[0]

            elif nonDim in mesh.specialSets.keys():
                nonDim = mesh.specialSets[nonDim]

                intMeshNd = uw.utils.Integral(
                    1.,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                intFieldNd = uw.utils.Integral(
                    scalarField,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                self.nonDimVal = lambda: \
                    intMeshNd.evaluate()[0] \
                    / intFieldNd.evaluate()[0]

            elif nonDim == "volume":

                intMeshNd = uw.utils.Integral(1., mesh)
                intFieldNd = uw.utils.Integral(scalarField, mesh)

                self.nonDimVal = lambda: \
                    intFieldNd.evaluate()[0] \
                    / intMeshNd.evaluate()[0]

            else:

                self.nonDimVal = lambda: 1.

        def evaluate(self):

            result = self.val() / self.nonDimVal()

            return result

    class Gradient:

        def __init__(self, scalarField, mesh, surface, nonDim = 1.):

            intFieldSurfGrad = uw.utils.Integral(
                fn.math.dot(mesh.unitvec_r_Fn, scalarField.fn_gradient),
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = surface
                )

            intMeshSurf = uw.utils.Integral(
                1.,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = surface
                )

            self.val = lambda: \
                -intFieldSurfGrad.evaluate()[0] \
                / intMeshSurf.evaluate()[0]

            if type(nonDim) == int or type(nonDim) == float:

                self.nonDimVal = lambda: float(nonDim)

            elif type(nonDim) == uw.mesh._mesh.FeMesh_IndexSet:

                intMeshNd = uw.utils.Integral(
                    1.,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                intFieldNd = uw.utils.Integral(
                    scalarField,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                self.nonDimVal = lambda: \
                    intMeshNd.evaluate()[0] \
                    / intFieldNd.evaluate()[0]

            elif nonDim == "volume":

                intMeshNd = uw.utils.Integral(1., mesh)
                intFieldNd = uw.utils.Integral(scalarField, mesh)

                self.nonDimVal = lambda: \
                    intFieldNd.evaluate()[0] \
                    / intMeshNd.evaluate()[0]

        def evaluate(self):

            result = -self.val() / self.nonDimVal()

            return result

    class ScalarFieldAverage:

        def __init__(self, scalarField, mesh, nonDim = 1.):

            intField = uw.utils.Integral(scalarField, mesh)

            intMesh = uw.utils.Integral(1., mesh)

            self.val = lambda: \
                intField.evaluate()[0] \
                / intMesh.evaluate()[0]

            if type(nonDim) == int or type(nonDim) == float:

                self.nonDimVal = lambda: float(nonDim)

            elif type(nonDim) == uw.mesh._mesh.FeMesh_IndexSet:

                intMeshNd = uw.utils.Integral(
                    1.,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                intFieldNd = uw.utils.Integral(
                    scalarField,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = nonDim
                    )

                self.nonDimVal = lambda: \
                    intFieldBase.evaluate()[0] \
                    / intMeshBase.evaluate()[0]

        def evaluate(self):

            result = self.val() / self.nonDimVal()

            return result

    class VectorFieldVolRMS:

        def __init__(self, vectorField, mesh):

            self.intVdotV = uw.utils.Integral(
                fn.math.dot(vectorField, vectorField),
                mesh
                )
            self.intMesh = uw.utils.Integral(
                1.,
                mesh
                )

        def evaluate(self):

            vectorIntegrated = self.intVdotV.evaluate()[0]
            meshIntegrated = self.intMesh.evaluate()[0]
            ratio = vectorIntegrated / meshIntegrated
            fieldrms = math.sqrt(ratio)

            return fieldrms

    class VectorFieldSurfRMS:

        def __init__(self, vectorField, mesh, indexSet):

            self.intVdotV = uw.utils.Integral(
                fn.math.dot(vectorField, vectorField),
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet
                )
            self.intMesh = uw.utils.Integral(
                1.,
                mesh,
                integrationType = 'surface',
                surfaceIndexSet = indexSet          
                )

        def evaluate(self):

            vectorIntegrated = self.intVdotV.evaluate()[0]
            meshIntegrated = self.intMesh.evaluate()[0]
            ratio = vectorIntegrated / meshIntegrated
            fieldrms = math.sqrt(ratio)

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
        self.keys = sorted(analyserDict, key=str.lower)
        self.header = ', '.join(self.keys)
        self.dataDict = {}
        self.data = [None] * len(self.keys)
        self.name = name
        self.dataBrief = "No data."

    def analyse(self):
        for key in self.keys:
            self.dataDict[key] = self.analyserDict[key].evaluate()
        self.data = [self.dataDict[key] for key in self.keys]
        self.dataBrief = [
            (key, self.formatDict[key].format(self.dataDict[key])) \
            for key in self.keys
            ]

    def report(self):

        if rank == 0:
            for pair in self.dataBrief:
                print(pair[0], pair[1])

class DataCollector:

    def __init__(self, analysers):

        self.analysers = analysers
        self.headers = [analyser.header for analyser in self.analysers]
        self.names = [analyser.name for analyser in self.analysers]
        self.datasets = [[] for analyser in self.analysers]

    def collect(self, refresh = False):

        for index, analyser in enumerate(self.analysers):
            if refresh:
                analyser.analyse()
            self.datasets[index].append(analyser.data)

    def out(self, clear = False):

        outdata = []
        for name, header, dataset in zip(self.names, self.headers, self.datasets):
            if len(dataset) > 0:
                dataArray = np.vstack(dataset)
            else:
                dataArray = None
            outdata.append((name, header, dataArray))
        if clear:
            self.datasets = [[] for analyser in self.analysers]
        return outdata

    def clear(self):
        return self.out(clear = True)