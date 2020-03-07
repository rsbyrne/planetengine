import numpy as np

from underworld import function as fn

from everest import mpi

from planetengine.observers import Observer
from planetengine.functions import \
    integral, gradient, operations, \
    component, getstat, comparison, \
    surface, split, tensor, \
    fourier, stream, conduction
from planetengine.visualisation.raster import Raster
from planetengine.visualisation.quickfig import QuickFig

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            velKey = 'velocityField',
            vcKey = 'vc',
            pressureKey = 'pressureField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
            heatingKey = 'heatingFn',
            diffKey = 'diffusivityFn',
            aspectKey = 'aspect',
            fluxKey = 'flux',
            **kwargs
            ):

        analysers = dict()
        baselines = dict()
        rasterArgs = []

        temp = observee.locals[tempKey]

        mesh = temp.mesh
        flux = observee.locals[fluxKey]
        diff = observee.locals[diffKey]
        heating = observee.locals[heatingKey]
        if flux is None:
            cond = conduction.default(temp, heating, diff)
        else:
            cond = conduction.inner(temp, heating, diff, flux)

        baselines['condTemp'] = integral.volume(cond).evaluate()
        adiabatic, conductive = gradient.rad(temp), gradient.rad(cond)
        thetaGrad = adiabatic / conductive
        Nu = integral.outer(thetaGrad)
        analysers['Nu'] = Nu
        thetaGradOuter = surface.outer(thetaGrad)
        analysers['Nu_min'] = getstat.mins(thetaGradOuter)
        analysers['Nu_range'] = getstat.ranges(thetaGradOuter)
        NuFreq = fourier.default(thetaGradOuter)
        analysers['Nu_freq'] = NuFreq

        theta = temp - cond
        avTemp = integral.volume(temp)
        avTheta = integral.volume(theta)
        analysers['theta_av'] = avTheta
        analysers['theta_min'] = getstat.mins(theta)
        analysers['theta_range'] = getstat.ranges(theta)
        rasterArgs.append(theta)

        vel = observee.locals[velKey]
        vc = observee.locals[vcKey]
        velMag = component.mag(vel)
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = VRMS
        analysers['velMag_range'] = getstat.ranges(velMag)
        velAng = component.ang(vel)
        velAngOuter = surface.outer(velAng)
        analysers['velAng_outer_av'] = integral.outer(velAng)
        analysers['velAng_outer_min'] = getstat.mins(velAngOuter)
        analysers['velAng_outer_range'] = getstat.ranges(velAngOuter)

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            if not type(visc) is fn.misc.constant:
                avVisc = integral.volume(visc)
                analysers['visc_av'] = avVisc
                analysers['visc_min'] = getstat.mins(visc)
                analysers['visc_range'] = getstat.ranges(visc)
        else:
            visc = 1.
        if plasticViscKey in observee.locals.__dict__:
            plastic = observee.locals[plasticViscKey]
            if not type(plastic) is fn.misc.constant:
                yielding = comparison.isequal(visc, plastic)
                yieldFrac = integral.volume(yielding)
                analysers['yieldFrac'] = yieldFrac

        pressure = observee.locals[pressureKey]
        stressRad = 2. * visc * gradient.rad(component.rad(vel)) - pressure
        stressAng = 2. * visc * gradient.ang(component.ang(vel)) - pressure
        stressRadOuter = surface.outer(stressRad)
        stressAngOuter = surface.outer(stressAng)
        analysers['stressRad_outer_av'] = integral.outer(stressRad)
        analysers['stressRad_outer_min'] = getstat.mins(stressRadOuter)
        analysers['stressRad_outer_range'] = getstat.ranges(stressRadOuter)
        analysers['stressAng_outer_av'] = integral.outer(stressAng)
        analysers['stressAng_outer_min'] = getstat.mins(stressAngOuter)
        analysers['stressAng_outer_range'] = getstat.ranges(stressAngOuter)

        strainRate = 2. * tensor.second_invariant(
            tensor.symmetric(gradient.default(vc))
            )
        strainRate_outer = surface.outer(strainRate)
        analysers['strainRate_outer_av'] = integral.outer(strainRate)
        analysers['strainRate_outer_min'] = getstat.mins(strainRate)
        analysers['strainRate_outer_range'] = getstat.ranges(strainRate)
        rasterArgs.append(strainRate)

        streamFn = stream.default(vc)
        analysers['psi_av'] = integral.volume(streamFn)
        analysers['psi_min'] = getstat.mins(streamFn)
        analysers['psi_range'] = getstat.ranges(streamFn)
        rasterArgs.append(streamFn)

        aspect = observee.locals[aspectKey]
        raster = Raster(*rasterArgs, aspect = aspect)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        self.baselines = baselines

        visVars = [temp, vel]
        if not visc == 1:
            visVars.append(operations.log(visc))
        self.visVars = visVars

        super().__init__(baselines = self.baselines, **kwargs)

        self.set_freq(10)

CLASS = Basic
