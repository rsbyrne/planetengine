name = 'test'
outputPath = '.'

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath)
# from everest.disk import purge_logs
# purge_logs()

from planetengine.systems.viscoplastic import Viscoplastic
from planetengine.observers.basic import Basic
from planetengine.campaign import Campaign

space = {
    'innerMethod': 'mg',
    'res': 32,
    'eta0': 1.,
    'tau0': 1.,
    'tau1': 0.,
    'alpha': [10 ** (x / 2) for x in range(7, 13)],
    'f': [x / 10. for x in range(5, 11)],
    }

mycampaign = Campaign(Viscoplastic, space, None, 100, 10, [Basic,], 2)

mycampaign()
