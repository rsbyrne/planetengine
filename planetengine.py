
# coding: utf-8

# In[1]:


import numpy as np
import underworld as uw
from underworld import function as fn
import math
import time


# In[5]:


class RuntimeCondition():

    class CombinedCondition():
        def __init__(self, arg, tupleOfFunctions):
            self.tupleOfFunctions = tupleOfFunctions
            self.arg = arg
        def evaluate(self, MODEL):
            boolList = [function.evaluate(MODEL) for function in self.tupleOfFunctions]
            antiBoolList = [not x for x in boolList]
            if self.arg == 'all':
                return all(boolList)
            elif self.arg == 'none':
                return all(antiBoolList)
            elif self.arg == 'any':
                return not all(antiBoolList)
            else:
                print "CombinedCondition argument not recognised"

    class UponCompletion():
        def __init__(self, TrueOrFalse):
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            if MODEL.MISC.modelrunComplete:
                return self.TrueOrFalse
            else:
                return not self.TrueOrFalse

    class ConstantBool():
        def __init__(self, arg):
            self.arg = arg
        def evaluate(self, MODEL):
            return self.arg

    class StepInterval():
        def __init__(self, stepInterval, TrueOrFalse):
            self.stepInterval = stepInterval
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            currentStep = MODEL.MISC.currentStep
            if currentStep % self.stepInterval == 0:
                return self.TrueOrFalse
            else:
                return not self.TrueOrFalse

    class TimeInterval():
        def __init__(self, timeInterval, TrueOrFalse):
            self.timeInterval = timeInterval
            self.lastTimeOut = 0.
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            currentTime = MODEL.MISC.currentTime
            if currentTime > self.lastTimeOut + self.timeInterval:
                self.lastTimeOut += self.timeInterval
                return self.TrueOrFalse
            else:
                return not self.TrueOrFalse

    class EpochTimeInterval():
        def __init__(self, timeInterval):
            self.timeInterval = timeInterval
            self.lastTimeOut = 0.
        def evaluate(self, MODEL):
            if MODEL.MISC.runningEpochTime > self.lastTimeOut + self.timeInterval:
                self.lastTimeOut += self.timeInterval
                return True
            else:
                return False

    class AfterStep():
        def __init__(self, targetStep, TrueOrFalse):
            self.targetStep = targetStep
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            currentStep = MODEL.MISC.currentStep
            if currentStep == self.targetStep:
                return self.TrueOrFalse
            elif currentStep < self.targetStep:
                return not self.TrueOrFalse
            else:
                return self.TrueOrFalse

    class AfterTime():
        def __init__(self, targetTime, TrueOrFalse):
            self.targetTime = targetTime
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            currentTime = MODEL.MISC.currentTime
            if currentTime > self.targetTime:
                return self.TrueOrFalse
            else:
                return not self.TrueOrFalse

    class AfterEpochTimeDuration():
        def __init__(self, timeCheck, TrueOrFalse):
            self.timeCheck = timeCheck
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            if MODEL.MISC.runningEpochTime < self.timeCheck:
                return not self.TrueOrFalse
            else:
                return self.TrueOrFalse

    class SteadyStateCriterion_1():
        def __init__(self, keytuple, timeHorizon, threshold, TrueOrFalse):
            self.keytuple = keytuple
            self.timeHorizon = timeHorizon
            self.threshold = threshold
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            if MODEL.MISC.freshData:
                print "Fresh data is available - checking steady state criterion..."
                isSteady = CheckSteadyState_1(MODEL.DATA, self.keytuple, self.timeHorizon, self.threshold)
                if isSteady:
                    return self.TrueOrFalse
                else:
                    return not self.TrueOrFalse
            else:
                return not self.TrueOrFalse

    class SteadyStateCriterion_2():
        def __init__(self, key, timeHorizon, threshold, TrueOrFalse):
            self.key = key
            self.timeHorizon = timeHorizon
            self.threshold = threshold
            self.TrueOrFalse = TrueOrFalse
        def evaluate(self, MODEL):
            if MODEL.MISC.freshData:
                print "Fresh data is available - checking steady state criterion..."
                isSteady = CheckSteadyState_2(MODEL.DATA, self.key, self.timeHorizon, self.threshold)
                if isSteady:
                    print "Steady state achieved!"
                    return self.TrueOrFalse
                else:
                    print "Steady state not yet achieved."
                    return not self.TrueOrFalse
            else:
                print "No fresh data available."
                return not self.TrueOrFalse


# In[99]:


class CoordSystems():

    class Radial():

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


# In[ ]:


class InitialConditions():
    
    class Group():

        def __init__(self, listofICs):
            self.listofICs = listofICs

        def apply_condition(self):
            for condition in self.listofICs:
                condition.apply_condition()

    class NoisyGradient():

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

        def apply_condition(self):
            #tempGradFn = depthFn * self.gradient * (self.range[1] - self.range[0]) + self.range[0]
            #field.data[:] = CapValue(randomise(self.smoothness, self.randomSeed) * tempGradFn.evaluate(mesh), self.range)
            tempGradFn = depthFn * self.gradient * (self.valRange[1] - self.valRange[0]) + self.valRange[0]
            initialTempFn = uw.function.branching.conditional([
                (depthFn == 0., self.valRange[0]),
                (depthFn == 1., self.valRange[1]),
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

    class LoadField():

        def __init__(
                self,
                field = None,
                filename = None,
                interpolate = True
                ):
            self.field = field
            self.filename = filename
            self.interpolate = interpolate

        def apply_condition(self):
            self.field.load(
                self.filename,
                interpolate = self.interpolate
                )

    class Sinusoidal():

        def __init__(
                self, variableArray, coordArray,
                pert = 0.2,
                freq = 1.,
                tempRange = (0., 1.),
                phase = 0.,
                ):
            self.variableArray = variableArray
            self.coordArray = coordArray
            self.freq = freq
            self.tempRange = tempRange
            self.phase = phase
            self.pert = pert

        def sinusoidal_IC(self):
            boxLength = np.max(self.coordArray[:,0]) - np.min(self.coordArray[:,0])
            boxHeight = np.max(self.coordArray[:,1]) - np.min(self.coordArray[:,1])
            tempMin, tempMax = self.tempRange
            deltaT = self.tempRange[1] - self.tempRange[0]
            pertArray = self.pert * np.cos(np.pi * (self.phase + self.freq * self.coordArray[:,0])) * np.sin(np.pi * self.coordArray[:,1])
            outArray = tempMin + deltaT * (boxHeight - self.coordArray[:,1]) + pertArray
            outArray = np.clip(outArray, tempMin, tempMax)
            outArray = np.array([[item] for item in outArray])
            return outArray

        def apply_condition(self):
            self.variableArray[:] = self.sinusoidal_IC()

    class Extents():

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

        def apply_condition(self):
            self.variableArray[:] = self.initial_extents()
            

    class Indices():

        def __init__(self, variableArray, indexControls, boundaries = None):
            self.variableArray = variableArray
            self.indexControls = indexControls

        def apply_condition(self):
            for indices, val in self.indexControls:
                self.variableArray[indices] = val

    class SetVal():

        def __init__(self, variableArray, val):
            self.variableArray = variableArray
            self.val = val

        def apply_condition(self):
            if type(self.variableArray) == list:
                for array in self.variableArray:
                    array[:] = self.val
            else:
                self.variableArray[:] = self.val

class Analysis():

    class Analyse():

        class asdfDimensionlessGradient():

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

        class DimensionlessGradient():

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

        class ScalarFieldAverage():

            def __init__(self, field, mesh):

                self.intField = uw.utils.Integral(field, mesh)
                self.intMesh = uw.utils.Integral(1., mesh)

            def evaluate(self):

                average = self.intField.evaluate()[0] \
                    / self.intMesh.evaluate()[0]
                return average

        class VectorFieldVolRMS():

            def __init__(self, vectorField, mesh):

                self.intVdotV = uw.utils.Integral(
                    fn.math.dot(vectorField, vectorField), mesh)
                self.intMesh = uw.utils.Integral(1., mesh)

            def evaluate(self):

                fieldrms = math.sqrt(self.intVdotV.evaluate()[0]) \
                    / self.intMesh.evaluate()[0]
                return fieldrms

        class VectorFieldSurfRMS():

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

        class Constant():

            def __init__(self, constant):

                self.constant = constant

            def evaluate(self):

                return self.constant

        class ArrayStripper():

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

    class Analyser():

        def __init__(self, name, analyserDict):

            self.analyserDict = analyserDict
            self.header = sorted(analyserDict.keys(), key=str.lower)
            self.headerStr = ', '.join(self.header)
            self.dataDict = {}
            self.data = [None] * len(self.header)
            self.name = name

        def update(self):

            for key in self.analyserDict:
                self.dataDict[key] = self.analyserDict[key].evaluate()
            self.data = [self.dataDict[key] for key in self.header]

        def evaluate(self):

            self.update()
            return self.data

    class DataCollector():

        def __init__(self, analysers):

            self.analysers = analysers
            self.headers = [analyser.headerStr for analyser in self.analysers]
            self.names = [analyser.name for analyser in self.analysers]
            self.datasets = [[] for analyser in self.analysers]

        def update(self):

            for index, analyser in enumerate(self.analysers):
                self.datasets[index].append(analyser.data)

        def clear(self):

            if not self.datasets == [[]]:
                outdata = []
                for name, headerStr, dataset in zip(self.names, self.headers, self.datasets):
                    dataArray = np.vstack(dataset)
                    outdata.append((name, headerStr, dataArray))
                self.datasets = [[] for analyser in self.analysers]
                return outdata

    class Report():

        def __init__(self, dataDict, formatDict, fig = None):

            self.dataDict = dataDict
            self.formatDict = formatDict
            self.fig = fig

        def report(self):
            keys = sorted(self.dataDict.keys(), key = str.lower)
            databrief = [(key, self.formatDict[key].format(self.dataDict[key])) for key in keys]
            if uw.rank() == 0:
                print databrief
                if not self.fig == None:
                    self.fig.show()

class Checkpointer():

    def __init__(
            self,
            outputPath = "",
            extension = '.csv',
            mode = 'ab',
            figs = None,
            varsOfState = None,
            dataCollector = None,
            step = None,
            ):

        # 'figs', 'varsOfState', and 'data' should be of the format
        # [(name, thing), (...,...), ...]
        self.outputPath = outputPath
        self.figs = figs
        self.varsOfState = varsOfState
        self.dataCollector = dataCollector
        self.mode = mode
        self.step = step

    def checkpoint(self):
        
        if uw.rank() == 0:
            print "Checkpointing..."
        if type(self.step) == None:
            stepStr = ""
        else:
            step = self.step.value
            stepStr = "_" + str(step).zfill(8)
        for name, fig in self.figs:
            fig.save(self.outputPath + name + stepStr)
        for row in self.varsOfState:
            variablePairs, substratePair = row
            substrate, substrateName = substratePair
            handle = substrate.save(self.outputPath + substrateName + stepStr + ".h5")
            for pair in variablePairs:
                variable, varName = pair
                variable.save(self.outputPath + varName + stepStr + ".h5", handle)
        if uw.rank() == 0:
            for row in self.dataCollector.clear():
                name, headerStr, dataArray = row
                filename = self.outputPath + name + '.csv'
                with open(filename, self.mode) as openedfile:
                    np.savetxt(openedfile, dataArray,
                        delimiter = ",",
                        header = headerStr
                        )
        if uw.rank() == 0:
            print "Checkpointed!"