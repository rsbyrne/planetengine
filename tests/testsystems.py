from .. import systems
from .. import initials

def get_system():
    system = systems.arrhenius.build(res = 32)
    ICs = {'temperatureField': initials.sinusoidal.build(freq = 1.)}
    system.initialise(ICs)
    return system
