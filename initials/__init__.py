import planetengine.initials.sinusoidal
import planetengine.initials.extents
import planetengine.initials.load

def apply(
        initial,
        system,
        ):
    for varName in sorted(system.varsOfState):
        var = system.varsOfState[varName]
        IC = initial[varName]
        IC.apply(var)
    system.step.value = 0
    system.modeltime.value = 0.