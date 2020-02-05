from everest import mpi
import os
if mpi.rank == 0:
    if os.path.exists('./test.frm'):
        os.remove('./test.frm')

from planetengine.systems import isovisc
from everest.builts.states import booloperator
from everest.builts import enactor, condition
from planetengine import quickShow

from everest.builts import set_global_anchor
set_global_anchor('test', '..')

real1 = isovisc.make(res = 16, Ra = 1e5)
threshold = booloperator.build(val = 10)
traverse = real1[threshold]
real2 = isovisc.make(res = 32, Ra = 1e5)
interop = booloperator.build(op = 'mod', val = 2, inv = True)
intercondition = condition.build(inquirer = interop, arg = real1)
myenactor = enactor.build(cycler = real2, condition = intercondition)
traverse.add_promptee(myenactor)
traverse()

print(real1.count, real2.count)
assert real1.count == real2.count * 2

import weakref

myref = weakref.ref(real1)

del real1
del threshold
del traverse
del real2
del interop
del intercondition
del myenactor

ref = myref()
print(ref, type(ref))
