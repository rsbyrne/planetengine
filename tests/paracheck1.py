raise Exception("Not up to date!")

from everest import mpi
import os

if mpi.rank == 0:
    if os.path.exists('./test.frm'):
        os.remove('./test.frm')

from planetengine.systems import isovisc
from planetengine import params
from planetengine import configs
from planetengine.initials import sinusoidal
from planetengine.initials import constant
from planetengine.states import threshold

system1 = isovisc.build(res = 16)
params1 = params.build(Ra = 1e5)
configs1 = configs.build(
    temperatureField = sinusoidal.build(),
    temperatureDotField = constant.build()
    )
state1 = threshold.build(val = 10)
traverse1 = system1[params1][configs1][state1]
system2 = isovisc.build(res = 32)
traverse2 = system2[params1][traverse1][state1]

traverse2()

traverse2.anchor('test', '.')

mpi.message(traverse2.arg.out())
mpi.message(traverse2.reader['*'])
mpi.message(traverse2.reader['*', '_count_'])
mpi.message("Complete!")

if mpi.rank == 0:
    if os.path.exists('./test.frm'):
        os.remove('./test.frm')
