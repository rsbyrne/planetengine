from .. import systems
from .. import initials

def get_system(**kwargs):
    system = systems.arrhenius.build(**kwargs)
    ICs = {'temperatureField': initials.sinusoidal.build(freq = 1.)}
    system.initialise(ICs)
    return system
