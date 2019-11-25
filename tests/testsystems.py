from .. import systems
from .. import initials

def getsystem(inSys = systems.arrhenius, **kwargs):
    system = inSys.build(**kwargs)
    ICs = {'temperatureField': initials.sinusoidal.build(freq = 1.)}
    system.initialise(ICs)
    return system

def isovisc(**kwargs):
    return getsystem(systems.isovisc, **kwargs)

def arrhenius(**kwargs):
    return getsystem(systems.arrhenius, **kwargs)
