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

task = isovisc(res = 32) \
    [params(Ra = 1e5)] \
    [configs(temperatureField = sinusoidal(), temperatureDotField = constant())] \
    [threshold(val = 10)]
# task.anchor('test', '..')

task()

task2 = isovisc(res = 64)\
    [params(Ra = 1e5)] \
    [configs(temperatureField = load(real = task.arg, varName = 'temperatureField'), temperatureDotField = constant())] \
    [threshold(val = 10)]
# task2.anchor('test', '..')
mpi.message("Complete!")
