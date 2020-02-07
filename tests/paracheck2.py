name = 'test'
outputPath = '..'
from everest import mpi
import os
fullpath = os.path.join(os.path.abspath(outputPath), name) + '.frm'
if mpi.rank == 0:
    if os.path.exists(fullpath):
        os.remove(fullpath)
from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)

message = mpi.message

from planetengine.systems import isovisc
from everest.builts.states import threshold
from everest.builts import perambulator
from everest.builts import enactor, condition
from planetengine import quickShow

real1 = isovisc.build(res = 16, Ra = 1e5)
traverse = perambulator.build(arg = real1, state = 10)
real2 = isovisc.build(res = 32, Ra = 1e5)
interop = threshold.build(op = 'mod', val = 2, inv = True)
intercondition = condition.build(inquirer = interop, arg = real1)
myenactor = enactor.build(cycler = real2, condition = intercondition)
traverse.add_promptee(myenactor)
traverse()

assert real1.count == real2.count * 2

import weakref

myref = weakref.ref(real1)

del real1
del traverse
del real2
del interop
del intercondition
del myenactor

# assert myref() is None
if not myref() is None:
    import gc
    referrers = gc.get_referrers(myref())
    print(sorted(referrers[0].keys()))
