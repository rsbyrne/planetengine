from .. import systems
from .. import initials

def get_system(inSys = systems.arrhenius, **kwargs):
    system = inSys.build(**kwargs)
    ICs = {'temperatureField': initials.sinusoidal.build(freq = 1.)}
    system.initialise(ICs)
    return system

def isovisc(**kwargs):
    return get_system(systems.isovisc, **kwargs)

def arrhenius(**kwargs):
    return get_system(systems.arrhenius, **kwargs)
