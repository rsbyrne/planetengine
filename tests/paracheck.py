import time

import planetengine
import everest
from everest.mpi import message

from planetengine.systems import isovisc

system = isovisc.build(Ra = 1e4, res = 16, f = 0.9)
system.iterate()
system.store()
system.iterate()
system.load(1)
system.iterate()
system.store()
system.store()
system.iterate()

import os
from everest import mpi
if mpi.rank == 0:
    if os.path.exists('test.frm'):
        os.remove('test.frm')
system.anchor('test', '.')
system.save()

system_identical = isovisc.build(Ra = 1e4, res = 16, f = 0.9)
# assert system_identical.constructor is system.constructor
assert system_identical.configs['temperatureField'] is system.configs['temperatureField']
assert system_identical is system

system2 = isovisc.build(Ra = 1e4, res = 16, f = 0.8)
# assert system2.constructor is system.constructor
assert system2.configs['temperatureField'] is system.configs['temperatureField']
assert not system2 is system
system.clear()
system.store()
system.save()
system.load(1)
system.store()
system.save()

# if mpi.rank == 0:
#     myfile = system.file()
#     assert system.constructor.hashID in myfile.keys()

from everest.builts import load

system_got = load(system.hashID, 'test', '.')
assert system_got is system

del everest.builts.Built._prebuilts[system.hashID]

system_loaded = load(system.hashID, 'test', '.')
assert not system_loaded is system
assert system_loaded.hashID == system.hashID
