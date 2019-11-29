from underworld import function as fn

from planetengine.observer import Observer
from planetengine.visualisation import Raster
from planetengine import functions as pfn

def build(*args, **kwargs):
    built = ObserveMS98(*args, **kwargs)
    return built

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

        inputs = locals().copy()

        outDict = {}

        temperature = system.obsVars[temperatureKey]
        avTemp = pfn.integral.default(temperature)
        tempGrad = pfn.gradient.rad(temperature)
        Nu = pfn.integral.outer(tempGrad) / pfn.integral.inner(temperature) * -1.
        velocity = system.obsVars[velocityKey]
        VRMS = pfn.operations.sqrt(
            pfn.integral.volume(
                pfn.operations.dot(
                    velocity,
                    velocity
                    )
                )
            )
        angVel = pfn.component.ang(velocity)
        radVel = pfn.component.rad(velocity)
        surfAngVel = pfn.integral.default(angVel)
        velMag = pfn.component.mag(velocity)
        strainSecInv = fn.tensor.second_invariant(
            fn.tensor.symmetric(
                velocity.fn_gradient
                )
            )
        viscosity = system.obsVars[viscosityKey]
        avVisc = pfn.integral.default(viscosity)
        avStrainSecInv = pfn.integral.default(strainSecInv)
        plasticity = system.obsVars[plasticityKey]
        avPlasticity = pfn.integral.default(plasticity)

        buoyancy = system.obsVars[buoyancyKey]
        rasterFns = [buoyancy, velMag, strainSecInv]
        raster = Raster(*rasterFns)
        self.raster = raster

        outDict['avTemp'] = avTemp
        outDict['Nu'] = Nu
        outDict['VRMS'] = VRMS
        outDict['surfAngVel'] = surfAngVel
        outDict['avVisc'] = avVisc
        outDict['avPlasticity'] = avPlasticity
        outDict['avStrainSecInv'] = avStrainSecInv
        outDict['raster'] = raster

        super().__init__(
            inputs = inputs,
            script = __file__,
            system = system,
            outDict = outDict
            )
