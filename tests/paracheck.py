import planetengine
import everest

from planetengine.systems import isovisc

system = isovisc.build(Ra = 1e4, res = 16, f = 0.9)

system.hashID

system.iterate()

system.store()

system.iterate()

system.load(1)

system.iterate()

system.store()

system.store()

system.iterate()

system.stored

import os
from everest import mpi
if mpi.rank == 0:
    if os.path.exists('test.frm'):
        os.remove('test.frm')
system.anchor('test', '.')

system.save()

system2 = isovisc.build()

system2 is system

system.clear()

system.stored

system.counts_disk

system.store()

system.counts_stored

system.save()

system.counts_stored

system.counts_disk

system.load(1)

system.store()

system.save()

system.counts_disk

system.constructor

from everest.builts import load
system_loaded = load(system.hashID, 'test', '..')

system_loaded is system

system.hashID

del system
del system_loaded
del everest.builts.BUILTS['igruajuupha-osfiagiobro']

from everest.builts import load
system_loaded = load('igruajuupha-osfiagiobro', 'test', '..')

system_loaded.hashID

system_loaded.constructor

new_system = system_loaded.constructor(Ra = 1e6, f = 0.7)

new_system.hashID

system_loaded.inputs

new_system.inputs
