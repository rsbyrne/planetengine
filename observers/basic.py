from underworld import function as fn

from planetengine.observers import Observer
from planetengine.functions import integral, gradient, operations, component
from planetengine.visualisation.raster import Raster

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            refTempKey = 'temperatureRefField',
            velKey = 'velocityField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
            **kwargs
            ):

        analysers = dict()

        temp = observee.locals[tempKey]
        refTemp = observee.locals[refTempKey]
        radGrad = gradient.rad(temp)
        surfInt = integral.outer(radGrad)
        radGradRef = gradient.rad(refTemp)
        surfIntRef = integral.outer(radGradRef)
        Nu = surfInt / surfIntRef
        analysers['Nu'] = self.Nu = Nu
        avT = integral.volume(temp)
        avTRef = integral.volume(refTemp)
        avTheta = avT - avTRef
        analysers['avT'] = self.avT = avT
        analysers['avTheta'] = self.avTheta = avTheta

        vel = observee.locals[velKey]
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = self.VRMS = VRMS

        visc = observee.locals[viscKey]
        avVisc = integral.volume(visc)
        analysers['avVisc'] = self.avVisc = avVisc
        creep = observee.locals['creepViscFn']
        yielding = integral.volume(visc < creep)
        analysers['yielding'] = self.yielding = yielding

        velMag = component.mag(vel)

        tempAnomaly = temp - refTemp
        plasticViscFn = observee.locals[plasticViscKey]
        logInvPlastic = operations.log(1. / plasticViscFn)
        stress = visc * vel
        logMagStress = operations.log(component.mag(stress))
        raster = Raster(tempAnomaly, logInvPlastic, logMagStress)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        super().__init__(**kwargs)

        self.set_freq(10)

CLASS = Basic
