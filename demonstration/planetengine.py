
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

def testfn():
    testvar = time.time()
    return testvar

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

def traverse(modelscript, options, params, stopCondition):
    model = modelscript.Handler(params, options)

def getDefaultKwargs(function):
    argsignature = inspect.signature(function)
    argbind = argsignature.bind()
    argbind.apply_defaults()
    argdict = dict(argbind.arguments)
    return argdict

class StopCondition:

    def __init__(self, stopFn, stopStr):
        self.stopFn = stopFn
        self.stopStr = stopStr
        self.status = "Running."

    def evaluate():
        if stopFn():
            self.status = self.stopStr
            return True
        else:
            return False

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

#class RuntimeConditions:

    #def __init__(self, listoftuples):

        #for condName, condStatement in listoftuples:
            #setattr(self, condName, self._Condition(condStatement))

    #class _Condition():

        #def __init__(self, fn):
            #self.fn = fn

        #def __call__(self):
            #return self.fn()

#class RuntimeConditions:

    #class Value:

        #def __init__(variable, value):
            #self.variable = variable
            #self.value = value

        #def evaluate(self):
            #return bool(variable == value)

    #class Group:

        #def __init__(pythonfunc, listofconditions):
            # pythonfunc can be any python function
            # that takes a list of objects
            # that have 'evaluate' methods that return a viable bool() input
            # and returns a value which is itself a viable bool() input
            #self.listofconditions = listofconditions
            #self.pythonfunc = pythonfunc

        #def evaluate(self):
            #listofbools = [bool(item.evaluate()) for item in listofconditions]
            #return bool(self.pythonfunc(self.listofbools))

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

class InitialConditions:
    
    class Group():

        def __init__(self, listofICs):
            self.listofICs = listofICs

        def apply(self):
            for condition in self.listofICs:
                condition.apply()

    class NoisyGradient:

        def __init__(
                self, variableArray, coordArray,
                gradient = 1.,
                smoothness = 1,
                randomSeed = 1066,
                valRange = (0., 1.)
                ):
            self.variableArray = variableArray
            self.coordArray = coordArray
            self.gradient = gradient
            self.smoothness = smoothness
            self.range = valRange
            self.randomSeed = randomSeed
            self.depthFn = 1. - fn.coord()[1]
            self.valRange = valRange

        def apply(self):
            #tempGradFn = depthFn * self.gradient * (self.range[1] - self.range[0]) + self.range[0]
            #field.data[:] = CapValue(randomise(self.smoothness, self.randomSeed) * tempGradFn.evaluate(mesh), self.range)
            tempGradFn = self.depthFn * self.gradient * (self.valRange[1] - self.valRange[0]) + self.valRange[0]
            initialTempFn = uw.function.branching.conditional([
                (self.depthFn == 0., self.valRange[0]),
                (self.depthFn == 1., self.valRange[1]),
                (tempGradFn < self.valRange[0], self.valRange[0]), # if this, that
                (tempGradFn > self.valRange[1] , self.valRange[1]), # otherwise, if this, this other thing
                (True, tempGradFn) # otherwise, this one
                ])
            self.variableArray = initialTempFn.evaluate(self.coordArray)
            # Introduce some random noise
            np.random.seed(self.randomSeed)
            for i in range(len(self.coordArray)):
                yCoord = self.coordArray[i][1]
                if 0 < yCoord < 1.:
                    randnum = 0.
                    smoothness = self.smoothness
                    for number in range(smoothness):
                        randnum += 2 * np.random.rand() / smoothness
                    randTemp = self.variableArray[i] * randnum
                    if self.range[0] < randTemp < self.range[1]:
                        self.variableArray[i] = randTemp

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

        def __init__(self, variableArray, val):
            self.variableArray = variableArray
            self.val = val

        def apply(self):
            if type(self.variableArray) == list:
                for array in self.variableArray:
                    array[:] = self.val
            else:
                self.variableArray[:] = self.val

class Analysis:

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

class Checkpointer:

    def __init__(
            self,
            modelName = "model",
            varsOfState = None,
            outputPath = "",
            scripts = None,
            instanceID = "test",
            figs = None,
            dataCollectors = None,
            inputs = None,
            step = None
            ):

        self.outputPath = outputPath
        self.scripts = scripts
        self.figs = figs
        self.dataCollectors = dataCollectors
        self.instanceID = instanceID
        self.varsOfState = varsOfState
        self.step = step
        self.modelName = modelName
        self.inputs = inputs

        self.outputDir = self.outputPath + self.modelName + self.instanceID + "/"

    def checkpoint(self):

        if uw.rank() == 0:
            if not os.path.isdir(self.outputDir):
                os.makedirs(self.outputDir)

                if not self.scripts is None:
                    for scriptname in self.scripts:
                        path = self.scripts[scriptname]
                        tweakedpath = os.path.splitext(path)[0] + ".py"
                        newpath = self.outputDir + "_" + scriptname + ".py"
                        shutil.copyfile(tweakedpath, newpath)

                inputFilename = self.outputDir + 'inputs.txt'
                with open(inputFilename, 'w') as file:
                     file.write(json.dumps(self.inputs))

        if uw.rank() == 0:
            print("Checkpointing...")

        if self.step is None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = str(step).zfill(8)

        self.checkpointDir = self.outputDir + stepStr + "/"

        if os.path.isdir(self.checkpointDir):
            if uw.rank() == 0:
                print('Checkpoint directory found: skipping.')
            return None
        else:
            if uw.rank() == 0:
                os.makedirs(self.checkpointDir)

        if uw.rank() == 0:
            print("Saving figures...")
        if not self.figs is None:
            for name in self.figs:
                fig = self.figs[name]
                fig.save(self.checkpointDir + name)
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Saving vars of state...")
        if not self.varsOfState is None:
            for row in self.varsOfState:
                variablePairs, substratePair = row
                substrateName, substrate = substratePair
                handle = substrate.save(self.checkpointDir + substrateName + ".h5")
                for pair in variablePairs:
                    varName, variable = pair
                    variable.save(self.checkpointDir + varName + ".h5", handle)
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Saving snapshot...")
            if not self.dataCollectors is None:
                for dataCollector in self.dataCollectors:
                    for index, name in enumerate(dataCollector.names):
                        dataArray = dataCollector.datasets[index][-1:]
                        headerStr = dataCollector.headers[index]
                        filename = self.checkpointDir + name + "_snapshot" + ".csv"
                        if not type(dataArray) == type(None):
                            with open(filename, 'w') as openedfile:
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = headerStr
                                    )
            print("Saved.")

        if uw.rank() == 0:
            print("Saving datasets...")
        if not self.dataCollectors is None:
            for dataCollector in self.dataCollectors:
                for row in dataCollector.clear():
                    if uw.rank() == 0:
                        name, headerStr, dataArray = row
                        filename = self.outputDir + name + '.csv'
                        if not type(dataArray) == type(None):
                            with open(filename, 'ab') as openedfile:
                                fileSize = os.stat(filename).st_size
                                if fileSize == 0:
                                    header = headerStr
                                else:
                                    header = ''
                                np.savetxt(openedfile, dataArray,
                                    delimiter = ",",
                                    header = header
                                    )
        if uw.rank() == 0:
            print("Saved.")

        if uw.rank() == 0:
            print("Checkpointed!")

class Model:

    def __init__(self, system, handler, initial,
        outputPath = '',
        instanceID = None,
        ):

        if instanceID == None:
            instanceID = "test" + "_" + time.strftime(
                '%y%m%d%H%M%SZ',time.gmtime(time.time())
                )

        self.system = system
        self.handler = handler
        self.initial = initial
        self.outputPath = outputPath
        self.instanceID = instanceID

        self.step = fn.misc.constant(0)
        self.modeltime = fn.misc.constant(0.)

        self.figs = self.handler.make_figs(system, self.step, self.modeltime)
        self.data = self.handler.make_data(system, self.step, self.modeltime)

        self.checkpointer = Checkpointer(
            step = self.step,
            varsOfState = self.system.varsOfState,
            figs = self.figs,
            dataCollectors = self.data.collectors,
            scripts = {
                'systemscript': self.system.script,
                'handlerscript': self.handler.script,
                'initialscript': self.initial.script,
                },
            inputs = {
                'params': self.system.inputs,
                'options': self.handler.inputs,
                'config': self.initial.inputs,
                },
            instanceID = self.instanceID,
            outputPath = self.outputPath,
            )

        self.reset()
        self.allDataRefreshed = False
        self.allDataCollected = False
        self.status = "ready"

    def checkpoint(self):
        if not self.allDataCollected:
            self.all_collect()
        self.checkpointer.checkpoint()

    def update(self):
        self.allDataRefreshed = False
        self.allDataCollected = False

    def all_analyse(self):
        for analyser in self.data.analysers:
            analyser.analyse()
        self.allDataRefreshed = True

    def report(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for analyser in self.data.analysers:
            analyser.report()
        for figname in self.figs:
            if uw.rank() == 0:
                print(figname)
            self.figs[figname].show()

    def reset(self):
        self.initial.apply(self.system)
        self.step.value = 0
        self.modeltime.value = 0.
        self.update()

    def all_collect(self):
        if not self.allDataRefreshed:
            self.all_analyse()
        for collector in self.data.collectors:
            collector.collect()
        self.allDataCollected = True

    def iterate(self):
        self.modeltime.value += self.system.iterate()
        self.step.value += 1
        self.update()

    def traverse(self, stopCondition,
            collectCondition = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            ):

        self.status = "pre-traverse"

        if checkpointCondition():
            self.checkpoint()

        while not stopCondition():

            self.status = "traversing"
            self.iterate()

            if checkpointCondition():
                self.checkpoint()
            elif collectCondition():
                self.all_collect()
                #for index, collector in enumerate(self.data.collectors):
                    #if type(collectConditions) == list:
                        #condition = collectConditions[index]()
                    #else:
                        #condition = collectConditions()
                    #if condition:
                        #collector.collect()

            if reportCondition():
                self.report()

        self.status = "post-traverse"

        if checkpointCondition():
            self.checkpoint()

        self.status = "ready"
