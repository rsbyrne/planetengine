from underworld import function as fn

from planetengine.observers import Observer
from planetengine.functions import integral, gradient, operations, component
from planetengine.visualisation.raster import Raster
from planetengine.visualisation.quickfig import QuickFig

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            condKey = 'conductionField',
            velKey = 'velocityField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
            creepViscKey = 'creepViscFn',
            **kwargs
            ):

        analysers = dict()

        temp = observee.locals[tempKey]
        cond = observee.locals[condKey]
        radGrad = gradient.rad(temp)
        surfInt = integral.outer(radGrad)
        radGradRef = gradient.rad(cond)
        surfIntRef = integral.outer(radGradRef)
        Nu = surfInt / surfIntRef
        analysers['Nu'] = self.Nu = Nu
        theta = temp - cond
        avTemp = integral.volume(temp)
        avTheta = integral.volume(theta)
        analysers['avTheta'] = self.avTheta = avTheta

        vel = observee.locals[velKey]
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = self.VRMS = VRMS
        # angVel = component.ang(vel)
        # surfVel = integral.outer(angVel)

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            avVisc = integral.volume(visc)
            analysers['avVisc'] = self.avVisc = avVisc
            creep = observee.locals[creepViscKey]
            self.yielding = yielding = visc < creep
            yieldFrac = integral.volume(yielding)
            analysers['yielding'] = self.yieldFrac = yieldFrac

        rasterArgs = []
        rasterArgs.append(theta)
        if plasticViscKey in observee.locals.__dict__:
            plasticViscFn = observee.locals[plasticViscKey]
            logInvPlastic = operations.log(1. / plasticViscFn)
            rasterArgs.append(logInvPlastic)
        if viscKey in observee.locals.__dict__:
            stress = visc * vel
            logMagStress = operations.log(component.mag(stress))
            rasterArgs.append(logMagStress)
        else:
            velMag = component.mag(vel)
            rasterArgs.append(velMag)
        raster = Raster(*rasterArgs)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        self.baselines = {
            'condTemp': integral.volume(cond).evaluate()
            }

        visVars = [temp, vel]
        try: visVars.append(visc)
        except NameError: pass
        try: visVars.append(yielding)
        except NameError: pass
        self.fig = QuickFig(*visVars)

        super().__init__(baselines = self.baselines, **kwargs)

        self.set_freq(10)

    def show(self):
        self.fig.show()

    def report(self):

        pass

CLASS = Basic
