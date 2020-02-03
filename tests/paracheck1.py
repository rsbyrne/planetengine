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

case1 = system1[params.build(Ra = 1e5)]

configuration = configs.build(
    temperatureField = sinusoidal.build(),
    temperatureDotField = constant.build()
    )
real1 = case1[configuration]

traverse1 = real1[threshold.build(val = 10)]

traverse1()

system2 = isovisc.build(res = 32, Ra = 1e6)

case2 = system2[case1.params]

real2 = case2[real1]

from planetengine import quickShow
quickShow(real2.locals.temperatureField)

traverse2 = real2[threshold.build(val = 5)]

system3 = isovisc.build(res = 64, Ra = 1e7)

case3 = system3[case2.params]

real3 = case3[traverse2]

traverse3 = real3[threshold.build(val = 3)]

traverse3()

traverse3.anchor('test', '.')

mpi.message(real3.out())
mpi.message(traverse3.reader['*'])
mpi.message(traverse3.reader['*', '_count_'])
mpi.message("Complete!")

if mpi.rank == 0:
    if os.path.exists('./test.frm'):
        os.remove('./test.frm')
