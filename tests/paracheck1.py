from everest import mpi
import os
if mpi.rank == 0:
    if os.path.exists('./test.frm'):
        os.remove('./test.frm')

from planetengine.systems.isovisc import build as isovisc
from planetengine.params import build as params
from planetengine.configs import build as configs
from planetengine.initials.sinusoidal import build as sinusoidal
from planetengine.initials.constant import build as constant
from planetengine.initials.load import build as load
from planetengine.states.threshold import build as threshold

system1 = isovisc(res = 32)
params1 = params(Ra = 1e5)
tempIC1 = sinusoidal()
tempDotIC1 = constant()
configs1 = configs(temperatureField = tempIC1, temperatureDotField = tempDotIC1)
threshold1 = threshold(val = 10)
case1 = system1[params1]
real1 = case1[configs1]
task1 = real1[threshold1]

system2 = isovisc(res = 64)
params2 = params(Ra = 1e6)
tempIC2 = load(real = task1.arg, varName = 'temperatureField')
tempDotIC2 = load(real = task1.arg, varName = 'temperatureDotField')
configs2 = configs(temperatureField = tempIC2, temperatureDotField = tempDotIC2)
threshold2 = threshold(val = 20)
case2 = system2[params1]
real2 = case2[configs2]
task2 = real2[threshold2]

task2.anchor('test', '.')

task2()

mpi.message(sorted(task2.reader['*'].keys()))

mpi.message("Complete!")
