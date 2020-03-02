name = 'test'
outputPath = '.'

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)
# from everest.disk import purge_logs
# purge_logs()

from planetengine.systems.MS98 import MS98
from planetengine.observers.basic import Basic
from planetengine.campaign import Campaign

space = {
    'res': 32,
    'eta0': 1.,
    'tau0': 1.,
    'tau1': 0.,
    'alpha': [10 ** (x / 2) for x in range(7, 13)],
    'f': [x / 10. for x in range(5, 11)],
    'aspect': [1., 1.2, 1.4, 1.6, 1.8, 2.]
    }

mycampaign = Campaign(MS98, space, 10, [Basic,], 2)

mycampaign()
