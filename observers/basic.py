from underworld import function as fn

from planetengine.observers import Observer
from planetengine.functions import integral, gradient, operations, component
from planetengine.visualisation.raster import Raster

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            velKey = 'velocityField',
            viscKey = 'viscosityFn',
            **kwargs
            ):

        analysers = dict()

        temp = observee.locals[tempKey]
        baseInt = integral.inner(temp)
        radGrad = gradient.rad(temp)
        surfInt = integral.outer(radGrad)
        Nu = surfInt / baseInt
        if 'f' in observee.inputs: Nu /= observee.inputs['f']
        analysers['Nu'] = self.Nu = Nu
        avT = integral.volume(temp)
        analysers['avT'] = self.avT = avT

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
        raster = Raster(temp, velMag, visc)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        super().__init__(**kwargs)

CLASS = Basic
