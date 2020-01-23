from underworld import function as fn

from planetengine.observer import Observer
from planetengine.visualisation import Raster
from planetengine import functions as pfn

class ObserveMS98(Observer):

    name = 'observeMS98'

    def __init__(
            self,
            system,
            temperatureKey = 'temperature',
            buoyancyKey = 'buoyancy',
            velocityKey = 'velocity',
            viscosityKey = 'viscosity',
            plasticityKey = 'plasticity'
            ):

        # inputs = locals().copy()

        outDict = {}

        temperature = pfn.convert(
            system.obsVars[temperatureKey],
            'temperature'
            )
        gradTemp = pfn.gradient.rad(temperature)
        avTemp = pfn.integral.default(temperature)
        Nu = \
            pfn.integral.outer(gradTemp) \
            / pfn.integral.inner(temperature) * -1.
        outDict['avTemp'] = avTemp
        outDict['Nu'] = Nu

        velocity = pfn.convert(
            system.obsVars[velocityKey],
            'velocity'
            )
        angVel = pfn.component.ang(velocity)
        # radVel = pfn.component.rad(velocity)
        # magVel = pfn.component.mag(velocity)
        surfAngVel = pfn.integral.outer(angVel)
        VRMS = pfn.operations.sqrt(
            pfn.integral.volume(
                pfn.operations.dot(
                    velocity,
                    velocity
                    )
                )
            )
        outDict['surfAngVel'] = surfAngVel
        outDict['VRMS'] = VRMS

        strainSecInv = fn.tensor.second_invariant(
            fn.tensor.symmetric(
                system.obsVars[velocityKey].fn_gradient
                )
            )
        strainSecInv = pfn.convert(
            strainSecInv,
            'strainSecInv'
            )
        avStrainSecInv = pfn.integral.default(strainSecInv)
        outDict['avStrainSecInv'] = avStrainSecInv

        viscosity = pfn.convert(
            system.obsVars[viscosityKey],
            'viscosity'
            )
        avVisc = pfn.integral.default(viscosity)
        outDict['avVisc'] = avVisc

        plasticity = system.obsVars[plasticityKey]
        avPlasticity = pfn.integral.default(plasticity)
        outDict['avPlasticity'] = avPlasticity

        stress = pfn.convert(
            system.obsVars[velocityKey] * system.obsVars[viscosityKey],
            'stress'
            )
        angStress = pfn.component.ang(stress)
        magStress = pfn.component.mag(stress)
        # radStress = pfn.component.rad(stress)
        # magStress = pfn.component.mag(stress)
        surfAngStress = pfn.integral.outer(angStress)
        outDict['surfAngStress'] = surfAngStress

        buoyancy = pfn.convert(
            system.obsVars[buoyancyKey],
            'buoyancy'
            )
        rasterFns = [buoyancy, magStress, strainSecInv]
        raster = Raster(*rasterFns)
        self.raster = raster
        outDict['raster'] = raster

        super().__init__(
            inputs = inputs,
            script = __file__,
            system = system,
            outDict = outDict
            )

### IMPORTANT ###
# from everest.builts import make_buildFn
CLASS = ObserveMS98
build = CLASS
