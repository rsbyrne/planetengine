from .. import systems
from .. import initials

def get_system():
    system = systems.arrhenius.build(res = 32)
    ICs = {'temperatureField': initials.sinusoidal.build(freq = 1.)}
    def reset():
        initials.apply(ICs, system)
        system.update()
    system.reset = reset
    system.reset()
    system.initials = ICs
    return system
