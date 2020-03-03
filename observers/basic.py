from underworld import function as fn

from planetengine.observers import Observer
from planetengine.functions import integral, gradient, operations, component
from planetengine.visualisation.raster import Raster

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            condKey = 'conductionField',
            velKey = 'velocityField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
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
        avTheta = integral.volume(theta)
        analysers['avTheta'] = self.avTheta = avTheta

        vel = observee.locals[velKey]
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = self.VRMS = VRMS

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            avVisc = integral.volume(visc)
            analysers['avVisc'] = self.avVisc = avVisc
            creep = observee.locals['creepViscFn']
            yielding = integral.volume(visc < creep)
            analysers['yielding'] = self.yielding = yielding

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

        super().__init__(**kwargs)

        self.set_freq(10)

CLASS = Basic
