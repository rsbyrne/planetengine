from planetengine.observers import Observer
from planetengine import functions as pfn

class Thermo(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            heatingKey = 'heatingFn',
            diffKey = 'diffusivityFn',
            fluxKey = 'flux',
            **kwargs
            ):

        analysers = dict()

        temp = observee.locals[tempKey]
        mesh = temp.mesh
        flux = observee.locals[fluxKey]
        diff = observee.locals[diffKey]
        heating = observee.locals[heatingKey]
        if flux is None:
            cond = pfn.conduction.default(temp, heating, diff)
        else:
            cond = pfn.conduction.inner(temp, heating, diff, flux)

        theta = temp - cond
        avTemp = pfn.integral.volume(temp)
        avTheta = pfn.integral.volume(theta)
        analysers['temp_av'] = avTemp
        analysers['temp_min'] = pfn.getstat.mins(temp)
        analysers['temp_range'] = pfn.getstat.ranges(temp)
        analysers['theta_av'] = avTheta
        analysers['theta_min'] = pfn.getstat.mins(theta)
        analysers['theta_range'] = pfn.getstat.ranges(theta)

        adiabatic, conductive = pfn.gradient.rad(temp), pfn.gradient.rad(cond)
        thetaGrad = adiabatic / conductive
        Nu = pfn.integral.outer(thetaGrad)
        analysers['Nu'] = Nu
        thetaGradOuter = pfn.surface.outer(thetaGrad)
        analysers['Nu_min'] = pfn.getstat.mins(thetaGradOuter)
        analysers['Nu_range'] = pfn.getstat.ranges(thetaGradOuter)
        NuFreq = pfn.fourier.default(thetaGradOuter)
        analysers['Nu_freq'] = NuFreq

        self.theta = theta
        self.cond = cond
        self.thetaGrad = thetaGrad
        self.thetaGradOuter = thetaGradOuter

        self.observee, self.analysers = observee, analysers

        self.visVars = [temp]

        super().__init__(**kwargs)

        self.set_freq(10)

CLASS = Thermo
