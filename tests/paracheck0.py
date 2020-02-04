import os
from everest import mpi

# # !!!!!!!!!!!!!!!!!!!!!!
# raise Exception("Fails due to link error.")
# # !!!!!!!!!!!!!!!!!!!!!!

if mpi.rank == 0:
    if os.path.exists('test.frm'):
        os.remove('test.frm')

from planetengine.systems import isovisc

system = isovisc.get(Ra = 1e4, res = 16, f = 0.9)
system.anchor('test', '.')

system.iterate()
system.store()
system.iterate()
system.load(1)
system.iterate()
system.store()
system.store()
system.iterate()

system.save()

system_identical = isovisc.get(Ra = 1e4, res = 16, f = 0.9)
assert system_identical.configs['temperatureField'] is system.configs['temperatureField']
assert system_identical is system

system2 = isovisc.get(Ra = 1e4, res = 16, f = 0.8)
assert system2.configs['temperatureField'] is system.configs['temperatureField']
assert not system2 is system
system.clear()
system.store()
system.save()
system.load(1)
system.store()
system.save()

from everest.builts import load
#
got_built = load(system.configs['temperatureField'].hashID, 'test', '.', get = True)
assert got_built is system.configs['temperatureField']

system_got = load(system.hashID, 'test', '.', get = True)
assert system_got is system

system_loaded = load(system.hashID, 'test', '.', get = False)
assert not system_loaded is system
assert system_loaded.hashID == system.hashID