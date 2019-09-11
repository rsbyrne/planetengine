from . import sinusoidal
from . import extents
from . import load

def apply(ICdict, system):
    for varName in sorted(ICdict):
        ICdict[varName].apply(system.varsOfState[varName])
