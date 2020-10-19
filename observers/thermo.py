from collections import OrderedDict

from planetengine import functions as pfn
from planetengine import fieldops
from planetengine.observers import PlanetObserver

class Thermo(PlanetObserver):

    def __init__(self,
            tempKey = 'temperatureField',
            heatingKey = 'heatingFn',
            diffKey = 'diffusivityFn',
            fluxKey = 'flux',
            aspectKey = 'aspect',
            res = 32,
            light = False,
            **kwargs
            ):
        super().__init__(**kwargs)

    @staticmethod
    def _construct(observables, i):

        print("thermo construct called")

        analysers = OrderedDict()

        aspect = observables.p[i.aspectKey]
        temp = observables[i.tempKey]
        flux = observables.p[i.fluxKey]
        diff = observables[i.diffKey]
        heating = observables[i.heatingKey]

        if flux is None:
            cond = pfn.conduction.default(temp, heating, diff)
        else:
            cond = pfn.conduction.inner(temp, heating, diff, flux)

        theta = temp - cond
        avTemp = pfn.integral.volume(temp)
        avTheta = pfn.integral.volume(theta)
        analysers['temp_av'] = avTemp
        analysers['temp_min'] = pfn.getstat.min(temp)
        analysers['temp_range'] = pfn.getstat.range(temp)
        analysers['theta_av'] = avTheta
        analysers['theta_min'] = pfn.getstat.min(theta)
        analysers['theta_range'] = pfn.getstat.range(theta)

        if not i.light:
            analysers['theta'] = fieldops.RegularData(
                pfn.rebase.zero(theta),
                size = (round(i.res * aspect), i.res)
                )

        adiabatic, conductive = pfn.gradient.rad(temp), pfn.gradient.rad(cond)
        thetaGrad = adiabatic / conductive
        Nu = pfn.integral.outer(thetaGrad)
        analysers['Nu'] = Nu
        thetaGradOuter = pfn.surface.outer(thetaGrad)
        analysers['Nu_min'] = pfn.getstat.min(thetaGradOuter)
        analysers['Nu_range'] = pfn.getstat.range(thetaGradOuter)
        NuFreq = pfn.fourier.default(thetaGradOuter)
        analysers['Nu_freq'] = NuFreq

        visVars = [temp]

        return locals()

CLASS = Thermo
