name = 'test'
outputPath = '.'

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)

from planetengine.systems.isovisc import Isovisc
from planetengine.campaign import Campaign

mycampaign = Campaign(
    schema = Isovisc,
    state = 3,
    cores = 2,
    res = 32,
    Ra = [10 ** (x / 2) for x in range(7, 13)],
    f = [x / 10. for x in range(5, 11)],
    aspect = [1., 1.2, 1.4, 1.6, 1.8, 2.]
    )

mycampaign()
