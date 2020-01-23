from planetengine.observer import Observer
from planetengine.visualisation import Raster
from planetengine import functions as pfn

class Standard(Observer):

    name = 'standard_iso'

    def __init__(
            self,
            system,
            temperatureKey = 'temperature',
            velocityKey = 'velocity',
            stressKey = 'stress'
            ):

        # inputs = locals().copy()

        outDict = {}
        rasterFns = []

        if temperatureKey in system.obsVars:
            temperature = system.obsVars[temperatureKey]
            avTemp = pfn.integral.default(temperature)
            tempGrad = pfn.gradient.rad(temperature)
            Nu = pfn.integral.outer(tempGrad) / pfn.integral.inner(temperature) * -1.
            outDict['avTemp'] = avTemp
            outDict['Nu'] = Nu
            rasterFns.append(temperature)
        if velocityKey in system.obsVars:
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
            outDict['VRMS'] = VRMS
            outDict['surfAngVel'] = surfAngVel
            velMag = pfn.component.mag(velocity)
            rasterFns.extend([angVel, radVel])
        raster = Raster(*rasterFns)
        outDict['raster'] = raster

        super().__init__(
            inputs = inputs,
            script = __file__,
            system = system,
            outDict = outDict
            )

### IMPORTANT ###
# from everest.builts import make_buildFn
CLASS = Standard
# build = make_buildFn(CLASS)
