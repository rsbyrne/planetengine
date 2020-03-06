import numpy as np

from underworld import function as fn

from everest import mpi

from planetengine.observers import Observer
from planetengine.functions import \
    integral, gradient, operations, \
    component, getstat, comparison, \
    surface, split, tensor, fourier
from planetengine.visualisation.raster import Raster
from planetengine.visualisation.quickfig import QuickFig

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            condKey = 'conductionField',
            velKey = 'velocityField',
            vcKey = 'vc',
            pressureKey = 'pressureField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
            **kwargs
            ):

        analysers = dict()
        baselines = dict()
        rasterArgs = []

        temp = observee.locals[tempKey]
        cond = observee.locals[condKey]
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
            avVisc = integral.volume(visc)
            analysers['visc_av'] = avVisc
            analysers['visc_min'] = getstat.mins(visc)
            analysers['visc_range'] = getstat.ranges(visc)
        else:
            visc = 1.
        if plasticViscKey in observee.locals.__dict__:
            plastic = observee.locals[plasticViscKey]
            yielding = comparison.isequal(visc, plastic)
            yieldFrac = integral.volume(yielding)
            analysers['yieldFrac'] = yieldFrac

        pressure = observee.locals[pressureKey]
        stressRad = 2. * visc * gradient.rad(component.rad(vel)) - pressure
        stressAng = 2. * visc * gradient.ang(component.ang(vel)) - pressure
        # stressMag = 2. * visc * gradient.mag(component.mag(vel)) - pressure
        stressRadOuter = surface.outer(stressRad)
        stressAngOuter = surface.outer(stressAng)
        analysers['stressRad_outer_av'] = integral.outer(stressRad)
        analysers['stressRad_outer_min'] = getstat.mins(stressRadOuter)
        analysers['stressRad_outer_range'] = getstat.ranges(stressRadOuter)
        analysers['stressAng_outer_av'] = integral.outer(stressAng)
        analysers['stressAng_outer_min'] = getstat.mins(stressAngOuter)
        analysers['stressAng_outer_range'] = getstat.ranges(stressAngOuter)
        rasterArgs.append(logVelMag)

        strainRate = 2. * tensor.second_invariant(
            tensor.symmetric(gradient.default(vc))
            )
        strainRate_outer = surface.outer(strainRate)
        analysers['strainRate_outer_av'] = integral.outer(strainRate)
        analysers['strainRate_outer_min'] = getstat.mins(strainRate)
        analysers['strainRate_outer_range'] = getstat.ranges(strainRate)
        logStrainRate = operations.log(strainRate)
        rasterArgs.append(strainRate)

        raster = Raster(*rasterArgs)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        self.baselines = baselines

        visVars = [temp, vel]
        if not visc == 1:
            visVars.append(visc)
        self.fig = QuickFig(*visVars)

        super().__init__(baselines = self.baselines, **kwargs)

        self.set_freq(10)

    def show(self):
        self.fig.show()

    def report(self):
        outs = self.out()
        outkeys = self.outkeys
        def dot_aligned(seq):
            snums = [str(n) for n in seq]
            dots = [len(s.split('.', 1)[0]) for s in snums]
            m = max(dots)
            return [' '*(m - d) + s for s, d in zip(snums, dots)]
        names, datas = [], []
        for name, data in zip(outkeys, outs):
            if data.shape == ():
                if name == 'count':
                    val = str(int(data))
                else:
                    val = "{:.2f}".format(data)
                justname = name.ljust(max([len(key) for key in outkeys]))
                names.append(justname)
                datas.append(val)
        datas = dot_aligned(datas)
        outlist = [name + ' : ' + data for name, data in zip(names, datas)]
        outstr = '\n'.join(outlist)
        mpi.message(outstr)

CLASS = Basic
