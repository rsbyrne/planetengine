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

from .meshutils import get_meshUtils
from .utilities import unpack_var
from .utilities import message
from.functions import _return

class Analyse:

    # class StandardIntegral:
    #     def __init__(
    #             var,
    #             opTags = None,
    #             updateFuncs = None,
    #             surface = 'volume'
    #             ):
    #
    #         varDict = unpack_var(var, detailed = True)
    #         var = varDict['var']
    #         mesh = varDict['mesh']
    #         meshUtils = get_meshUtils(mesh)
    #
    #         intMesh = meshUtils.integrals[surface]
    #         self.opTag = 'Integral_' + surface
    #         if surface == 'volume':
    #             intField = uw.utils.Integral(var, mesh)
    #         else:
    #             indexSet = pemesh.surfaces[surface]
    #             intField = uw.utils.Integral(
    #                 var,
    #                 mesh,
    #                 integrationType = 'surface',
    #                 surfaceIndexSet = indexSet
    #                 )
    #
    #         self.val = 0.
    #         self.lasthash = 0
    #
    #         def updateFunc():
    #             self.val = intField.evaluate()[0] \
    #                 / intMesh()
    #
    #         var, opTags, updateFuncs = _return(
    #             var, opTag, opTags, updateFunc, updateFuncs)
    #             )
    #
    #         ## Define the evalFn that makes everything go:
    #         self.evalFn = lambda: \
    #             intField.evaluate()[0] \
    #             / intMesh()
    #
    #         # Keeping house:
    #
    #         self.var = var
    #
    #         ## Finalise the opTag:
    #         self.opTag = self.opTag[:-1]
    #
    #         ## Get a starting value
    #         self.lasthash = 0
    #         self.val = self.evaluate()
    #
    #         ## Done!
    #         message("Integral built.")


#     class StandardIntegral:
#         '''
#         Takes Underworld variables and functions
#         and a variety of options and builds
#         integrals for data analysis.
#         inVar: the variable to be integrate.
#         - an Underworld variable or function based on a variable.
#         comp: for multi-dimensional fields, choose the component
#         to analyse. Defaults to the magnitude.
#         - None, 'ang', 'ang1', 'ang2', 'rad'.
#         gradient: choose the component of the gradient to integrate,
#         if any.
#         - None, 'ang', 'ang1', 'ang2', 'rad', 'mag'.
#         surface: choose the surface over which to integrate,
#         or integrate 'volume' by default.
#         - 'volume', 'outer', 'inner', 'left', 'right', 'front', 'back'.
#         nonDim: optionally nondimensionalise the integral using
#         another evaluable function.
#         - a callable that returns a double.
#         '''
#
#         def __init__(
#                 self,
#                 inVar,
#                 comp = None,
#                 gradient = None,
#                 bucket = None,
#                 quantile = None,
#                 surface = 'volume',
#                 nonDim = None,
#                 ):
#
#             message("Building integral...")
#
#             # Getting everything ready:
#
#             self.inputs = locals().copy()
#             del self.inputs['inVar']
#             del self.inputs['self']
#
#             self.updateFuncs = []
#
#             self.opTag = ''
#
#             pevar = standardise(inVar)
#             var = pevar.meshVar
#             self.updateFuncs.append(pevar.update)
#
#             mesh = pevar.mesh
#             pemesh = standardise(mesh)
#
#             # Check inputs: (Is this really necessary??)
#
#             ## Check that the dimension is sensible:
#             if not mesh.dim in {2, 3}:
#                 raise Exception
#             if not pevar.varDim in {1, mesh.dim}:
#                 raise Exception
#
#             ## Check 'comp' input is correct:
#             if pevar.vector:
#                 if mesh.dim == 2:
#                     if not comp in {None, 'ang', 'rad'}:
#                         raise Exception
#                 elif mesh.dim == 3:
#                     if not comp in {None, 'ang1', 'ang2', 'rad'}:
#                         raise Exception
#             else:
#                 if not comp is None:
#                     raise Exception
#
#             ## Check 'gradient' input is correct:
#             if not pevar.discrete:
#                 if mesh.dim == 2:
#                     if not gradient in {None, 'ang', 'rad'}:
#                         raise Exception
#                 elif mesh.dim == 3:
#                     if not gradient in {None, 'ang1', 'ang2', 'rad'}:
#                         raise Exception
#             else:
#                 if not gradient is None:
#                     raise Exception
#
# #             ## Check 'cutoff' input is correct:
# #             cutoffFn = uw.function.Function.convert(cutoff)
# #             if not cutoff is None:
# #                 if not isinstance(cutoffFn, uw.function.Function):
# #                     raise Exception
#
#             ## Check 'bucket' input is correct:
#             if not bucket is None:
#                 if not type(bucket) in {float, int}:
#                     pass
#                 elif type(bucket) is tuple:
#                     if len(bucket) == 2:
#                         for var in bucket:
#                             if type(var) in {float, int}:
#                                 pass
#                             elif type(var) is str:
#                                 if not (var == 'max' or var == 'min'):
#                                     raise Exception
#                             else:
#                                 raise Exception
#                     elif len(bucket) == 3:
#                         if not bucket[0] == 'quantile':
#                             raise Exception
#                         if not type(bucket[1]) is int and type(bucket[2]) is int:
#                             raise Exception
#
#             ## Check 'surface' input is correct:
#             if mesh.dim == 2:
#                 if not surface in {'volume', 'outer', 'inner', 'left', 'right'}:
#                     raise Exception
#             elif mesh.dim == 3:
#                 if not surface in {'volume', 'outer', 'inner', 'left', 'right', 'front', 'back'}:
#                     raise Exception
#
#             # Build the integral:
#
#             ## Add comp if required:
#             if pevar.vector:
#                 if comp is None:
#                     var = fn.math.sqrt(fn.math.dot(var, var))
#                 else:
#                     var = fn.math.dot(var, pemesh.comps[comp])
#                     self.opTag += comp + 'Comp_'
#
# #             ## Add cutoff if required:
# #             if not cutoff is None:
# #                 var = fn.branching.conditional([
# #                     (var >= cutoffFn - 1e-18, 1.),
# #                     (var <= cutoffFn + 1e-18, 1.),
# #                     (True, 0.),
# #                     ])
#
#             ## Add gradient if required:
#             if not gradient is None:
#                 var, project = pemesh.meshify(
#                     var,
#                     return_project = True
#                     )
#                 self.updateFuncs.append(project)
#                 varGrad = var.fn_gradient
#                 if gradient == 'mag':
#                     var = fn.math.sqrt(fn.math.dot(varGrad, varGrad))
#                 else:
#                     var = fn.math.dot(pemesh.comps[gradient], varGrad)
#                 self.opTag += gradient + 'Grad_'
#
#             ## Add bucket if required:
#             if not bucket is None:
#                 if type(bucket) is tuple:
#                     adjBucket = []
#                     for val in bucket:
#                         if type(val) is str:
#                             if val == 'max':
#                                 addVal = 1e18
#                             elif val == 'min':
#                                 addVal = 1e-18
#                             else:
#                                 raise Exception
#                         else:
#                             addVal = val
#                         adjBucket.append(addVal)
#                     bucketStr = str(bucket[0]) + ':' + str(bucket[1])
#                 else:
#                     adjBucket = (bucket - 1e-18, bucket + 1e-18)
#                     bucketStr = str(bucket)
#                 var = fn.branching.conditional([
#                     (var < adjBucket[0], 0.),
#                     (var > adjBucket[1], 0.), # double-open interval - is this a problem?
#                     (True, 1.),
#                     ])
#                 self.opTag += 'Bucket{' + bucketStr + '}_'
#
#             ## Do the integral over the desired surface:
#             intMesh = pemesh.integrals[surface]
#             self.opTag += surface + 'Int_'
#             if surface == 'volume':
#                 intField = uw.utils.Integral(var, mesh)
#             else:
#                 indexSet = pemesh.surfaces[surface]
#                 intField = uw.utils.Integral(
#                     var,
#                     mesh,
#                     integrationType = 'surface',
#                     surfaceIndexSet = indexSet
#                     )
#
#             ## Non-dimensionalise if specifed:
#             if nonDim is None:
#                 nonDim = lambda: 1.
#             else:
#                 self.opTag += 'nd_' + nonDim.opTag + '_'
#
#             ## Define the evalFn that makes everything go:
#             self.evalFn = lambda: \
#                 intField.evaluate()[0] \
#                 / intMesh() \
#                 / nonDim()
#
#             # Keeping house:
#
#             self.var = var
#
#             ## Finalise the opTag:
#             self.opTag = self.opTag[:-1]
#
#             ## Get a starting value
#             self.lasthash = 0
#             self.val = self.evaluate()
#
#             ## Done!
#             message("Integral built.")
#
#         def evaluate(self):
#             currenthash = utilities.hash_var(self.var)
#             if currenthash == self.lasthash:
# #                 message(
# #                     "No underlying change detected: \
# #                     skipping evaluation."
# #                     )
#                 return self.val
#             else:
#                 for updateFunc in self.updateFuncs:
#                     updateFunc()
#                 self.val = self.evalFn()
#                 self.lasthash = currenthash
#             return self.val
#
#         def __call__(self):
#             return self.evaluate()

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
            message(pair[0], pair[1])

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
