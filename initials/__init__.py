import planetengine.initials.sinusoidal
import planetengine.initials.extents
import planetengine.initials.load
from planetengine.utilities import setboundaries

def apply(initial, system):
    for varName in sorted(system.varsOfState):
        var = system.varsOfState[varName]
        IC = initial[varName]
        IC.apply(var)
        if varName in system.varScales:
            minVal, maxVal = system.varScales[varName]
            valRange = maxVal - minVal
            if hasattr(IC, 'inFrame'):
                if IC.sourceVarName in IC.inFrame.system.varScales:
                    in_minVal, in_maxVal = IC.inFrame.system.varScales[IC.sourceVarName]
                else:
                    # MAKE THIS MORE ROBUST
                    in_minVal, in_maxVal = (0., 1.)
                in_delta = in_maxVal - in_minVal
                var.data[:] = (var.data[:] - in_minVal) / in_delta
            var.data[:] = (var.data[:] + minVal) / valRange
        if varName in system.varBounds:
            boundaries = system.varBounds[varName]
            setboundaries(var, boundaries)
    system.step.value = 0
    system.modeltime.value = 0.