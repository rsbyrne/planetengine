import numpy as np

from underworld import function as fn

from planetengine import mpi
from planetengine.observers import Observer
from planetengine import functions as pfn
from planetengine.fieldops import RegularData
from window.raster import Raster

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
        rasterArgs = []

        temp = observee.locals[tempKey]

        mesh = temp.mesh
        flux = observee.locals[fluxKey]
        diff = observee.locals[diffKey]
        heating = observee.locals[heatingKey]
        if flux is None:
            cond = pfn.conduction.default(temp, heating, diff)
        else:
            cond = pfn.conduction.inner(temp, heating, diff, flux)

        adiabatic, conductive = pfn.gradient.rad(temp), pfn.gradient.rad(cond)
        thetaGrad = adiabatic / conductive
        Nu = pfn.integral.outer(thetaGrad)
        analysers['Nu'] = Nu
        thetaGradOuter = pfn.surface.outer(thetaGrad)
        analysers['Nu_min'] = pfn.getstat.min(thetaGradOuter)
        analysers['Nu_range'] = pfn.getstat.range(thetaGradOuter)
        NuFreq = pfn.fourier.default(thetaGradOuter)
        analysers['Nu_freq'] = NuFreq

        theta = temp - cond
        avTemp = pfn.integral.volume(temp)
        avTheta = pfn.integral.volume(theta)
        analysers['temp_av'] = avTemp
        analysers['temp_min'] = pfn.getstat.min(temp)
        analysers['temp_range'] = pfn.getstat.range(temp)
        analysers['theta_av'] = avTheta
        analysers['theta_min'] = pfn.getstat.min(theta)
        analysers['theta_range'] = pfn.getstat.range(theta)

        vel = observee.locals[velKey]
        vc = observee.locals[vcKey]
        velMag = pfn.component.mag(vel)
        VRMS = pfn.operations.sqrt(pfn.integral.volume(pfn.component.sq(vel)))
        analysers['VRMS'] = VRMS
        analysers['velMag_range'] = pfn.getstat.range(velMag)
        velAng = pfn.component.ang(vel)
        velAngOuter = pfn.surface.outer(velAng)
        analysers['velAng_outer_av'] = pfn.integral.outer(velAng)
        analysers['velAng_outer_min'] = pfn.getstat.min(velAngOuter)
        analysers['velAng_outer_range'] = pfn.getstat.range(velAngOuter)

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            if not type(visc) is fn.misc.constant:
                avVisc = pfn.integral.volume(visc)
                analysers['visc_av'] = avVisc
                analysers['visc_min'] = pfn.getstat.min(visc)
                analysers['visc_range'] = pfn.getstat.range(visc)
        else:
            visc = 1.
        if plasticViscKey in observee.locals.__dict__:
            plastic = observee.locals[plasticViscKey]
            if not type(plastic) is fn.misc.constant:
                yielding = pfn.comparison.isequal(visc, plastic)
                yieldFrac = pfn.integral.volume(yielding)
                analysers['yieldFrac'] = yieldFrac
                self.yielding = yielding

        pressure = observee.locals[pressureKey]
        stressRad = pfn.gradient.rad(pfn.component.rad(vel)) \
            * visc \
            * 2. \
            - pressure
        stressAng = pfn.gradient.ang(pfn.component.ang(vel)) \
            * visc \
            * 2. \
            - pressure
        stressRadOuter = pfn.surface.outer(stressRad)
        stressAngOuter = pfn.surface.outer(stressAng)
        analysers['stressRad_outer_av'] = pfn.integral.outer(stressRad)
        analysers['stressRad_outer_min'] = pfn.getstat.min(stressRadOuter)
        analysers['stressRad_outer_range'] = pfn.getstat.range(stressRadOuter)
        analysers['stressAng_outer_av'] = pfn.integral.outer(stressAng)
        analysers['stressAng_outer_min'] = pfn.getstat.min(stressAngOuter)
        analysers['stressAng_outer_range'] = pfn.getstat.range(stressAngOuter)

        strainRate = pfn.tensor.second_invariant(
            pfn.tensor.symmetric(pfn.gradient.default(vc))
            ) * 2.
        strainRate_outer = pfn.surface.outer(strainRate)
        analysers['strainRate_outer_av'] = pfn.integral.outer(strainRate)
        analysers['strainRate_outer_min'] = pfn.getstat.min(strainRate)
        analysers['strainRate_outer_range'] = pfn.getstat.range(strainRate)

        streamFn = pfn.stream.default(vc)
        analysers['psi_av'] = pfn.integral.volume(streamFn)
        analysers['psi_min'] = pfn.getstat.min(streamFn)
        analysers['psi_range'] = pfn.getstat.range(streamFn)

        aspect = observee.locals[aspectKey]
        rasterFns = [
            pfn.rebase.zero(theta),
            pfn.operations.sqrt(strainRate),
            pfn.rebase.zero(streamFn)
            ]
        size = [int(aspect) * 256, 256]
        bands = [RegularData(fn, size) for fn in rasterFns]
        raster = Raster(*bands)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers
        self.strainRate = strainRate
        self.streamFn = streamFn
        self.velMag = velMag
        self.theta = theta

        visVars = [temp, vel]
        if not visc == 1:
            visVars.append(pfn.operations.log(visc))
        self.visVars = visVars

        super().__init__(**kwargs)

        self.set_freq(10)

CLASS = Basic
