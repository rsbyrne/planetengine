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
from planetengine import unpack_var
from planetengine import standardise

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

class Analyse:

    class StandardIntegral:
        '''
        Takes Underworld variables and functions
        and a variety of options and builds
        integrals for data analysis.
        inVar: the variable to be integrate.
        - an Underworld variable or function based on a variable.
        comp: for multi-dimensional fields, choose the component
        to analyse. Defaults to the magnitude.
        - 'mag', 'ang', 'ang1', 'ang2', 'rad'.
        gradient: choose the component of the gradient to integrate,
        if any.
        - None, 'ang', 'ang1', 'ang2', 'rad', 'mag'.
        surface: choose the surface over which to integrate,
        or integrate 'volume' by default.
        - 'volume', 'outer', 'inner', 'left', 'right', 'front', 'back'.
        nonDim: optionally nondimensionalise the integral using
        another evaluable function.
        - a callable that returns a double.
        '''

        def __init__(
                self,
                inVar,
                comp = 'mag',
                gradient = None,
                surface = 'volume',
                nonDim = None,
                ):

            planetengine.message("Building integral...")

            self.inputs = locals().copy()
            del self.inputs['inVar']
            del self.inputs['self']

            self.opTag = ''

            unpacked = planetengine.unpack_var(inVar, return_dict = True)
            self.rawvar = unpacked['var']
            var = self.rawvar
            mesh = unpacked['mesh']
            pemesh = planetengine.standardise(mesh)

            if unpacked['varDim'] == mesh.dim:
                # hence is vector
                if comp == 'mag':
                    var = fn.math.sqrt(fn.math.dot(var, var))
                else:
                    var = fn.math.dot(var, pemesh.comps[comp])
                    self.opTag += comp + 'Comp_'
            else:
                assert unpacked['varDim'] == 1
                # hence is scalar.
                comp = 'mag'
                self.inputs['comp'] = comp

            if not gradient is None:

                var, self.project = pemesh.meshify(
                    var,
                    return_project = True
                    )
                varGrad = var.fn_gradient
                if gradient == 'mag':
                    var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
                else:
                    var = fn.math.dot(pemesh.comps[gradient], varGrad)

                self.opTag += gradient + 'Grad_'

            intMesh = pemesh.integrals[surface]
            self.opTag += surface + 'Int_'
            if surface == 'volume':
                intField = uw.utils.Integral(var, mesh)
            else:
                indexSet = pemesh.surfaces[surface]
                intField = uw.utils.Integral(
                    var,
                    mesh,
                    integrationType = 'surface',
                    surfaceIndexSet = indexSet
                    )

            if nonDim is None:
                nonDim = lambda: 1.
            else:
                self.opTag += 'nd_' + nonDim.opTag + '_'

            self.evalFn = lambda: \
                intField.evaluate()[0] \
                / intMesh() \
                / nonDim()

            self.opTag = self.opTag[:-1]

            self.lasthash = 0
            self.val = self.evaluate()

            planetengine.message("Integral built.")

        def evaluate(self):
            currenthash = planetengine.utilities.hash_var(self.rawvar)
            if currenthash == self.lasthash:
                planetengine.message(
                    "No underlying change detected: \
                    skipping evaluation."
                    )
                return self.val
            else:
                if hasattr(self, 'project'):
                    self.project()
                self.val = self.evalFn()
                self.lasthash = currenthash
            return self.val

        def __call__(self):
            return self.evaluate()

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

    def __init__(
            self,
            name,
            analyserDict,
            formatDict,
            step,
            modeltime,
            ):

        self.analyserDict = analyserDict
        self.formatDict = formatDict

        miscDict = {
            'step': Analyse.ArrayStripper(
                step,
                (0, 0),
                ),
            'modeltime': Analyse.ArrayStripper(
                modeltime,
                (0, 0),
                )
            }
        miscFormatDict = {
            'step': "{:.0f}",
            'modeltime': "{:.1E}",
            }
        self.analyserDict.update(miscDict)
        self.formatDict.update(miscFormatDict)

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
        self.analyse()
        for pair in self.dataBrief:
            planetengine.message(pair[0], pair[1])

class DataCollector:

    def __init__(self, analysers):

        self.analysers = analysers
        self.headers = [analyser.header for analyser in self.analysers]
        self.names = [analyser.name for analyser in self.analysers]
        self.datasets = [[] for analyser in self.analysers]

    def collect(self):

        for index, analyser in enumerate(self.analysers):
            analyser.analyse()
            if not analyser.data in self.datasets[index]:
                self.datasets[index].append(analyser.data)

    def out(self):

        outdata = []
        for name, header, dataset in zip(self.names, self.headers, self.datasets):
            if len(dataset) > 0:
                dataArray = np.vstack(dataset)
            else:
                dataArray = None
            outdata.append((name, header, dataArray))
        return outdata

    def clear(self):
        self.datasets = [[] for analyser in self.analysers]