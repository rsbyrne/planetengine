import planetengine.initials.sinusoidal
import planetengine.initials.extents
import planetengine.initials.load
from planetengine.utilities import setboundaries

def apply(initial, inputs):
    if hasattr(inputs, "sub_systems"):
        for system in inputs.sub_systems:
            _apply(initial, system)
    else:
        _apply(initial, inputs)

def _apply(initial, system):
    for varName in sorted(system.varsOfState):
        var = system.varsOfState[varName]
        IC = initial[varName]
        if hasattr(system, 'boxDims'):
            boxDims = system.boxDims
        else:
            boxDims = None
        try:
            IC.apply(var, boxDims)
        except:
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