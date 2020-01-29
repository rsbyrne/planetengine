from .. import systems
from .. import initials

def getsystem(inSys = systems.arrhenius, **kwargs):
    system = inSys.get(**kwargs)
    ICs = {'temperatureField': initials.sinusoidal.get(freq = 1.)}
    system.initialise(ICs)
    return system

def isovisc(**kwargs):
    return getsystem(systems.isovisc, **kwargs)

def arrhenius(**kwargs):
    return getsystem(systems.arrhenius, **kwargs)
