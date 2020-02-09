name = 'test'
outputPath = '.'
from everest import mpi
import os
# fullpath = os.path.join(os.path.abspath(outputPath), name) + '.frm'
# if mpi.rank == 0:
#     if os.path.exists(fullpath):
#         os.remove(fullpath)

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)

from planetengine.systems.isovisc import Isovisc
from planetengine.campaign import Campaign

mycampaign = Campaign(
    Isovisc, 100,
    res = 32,
    Ra = [10 ** (x / 2) for x in range(7, 13)],
    f = [x / 10. for x in range(5, 11)],
    aspect = [1., 1.2, 1.4, 1.6, 1.8, 2.]
    )

mycampaign()
