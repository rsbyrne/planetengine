name = 'test'
outputPath = '.'
from everest import mpi
import os
fullpath = os.path.join(os.path.abspath(outputPath), name) + '.frm'
if mpi.rank == 0:
    if os.path.exists(fullpath):
        os.remove(fullpath)

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)

from planetengine.systems.isovisc import Isovisc
from planetengine.campaign import Campaign

mycampaign = Campaign(Isovisc, 2, Ra = [1e4, 1e5], f = [0.5, 0.7])

mycampaign()
