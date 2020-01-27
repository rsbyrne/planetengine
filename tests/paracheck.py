import planetengine
import everest

from planetengine.systems import isovisc

system = isovisc.build(Ra = 1e4, res = 16, f = 0.9)
hashID = system.hashID
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
system2 = isovisc.build()
system.clear()
system.store()
system.save()
system.load(1)
system.store()
system.save()

from everest.builts import load
system_loaded = load(system.hashID, 'test', '..')

del system
del system_loaded
del everest.builts.BUILTS[hashID]

from everest.builts import load
system_loaded = load(hashID, 'test', '..')

new_system = system_loaded.constructor(Ra = 1e6, f = 0.7)
