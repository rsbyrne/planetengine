import sys
import os

import planetengine
disk = planetengine.disk
_built = planetengine._built
campaign = planetengine.campaign

path = os.path.dirname(__file__)

my_campaign = _built.load_built('campaign', path)

MODE = sys.argv[1] # single or auto
if MODE == 'single':
    JOBID = sys.argv[2]
    my_campaign._master_run(JOBID)
elif MODE == 'auto':
    CORES = sys.argv[2]
    my_campaign.autorun(cores = CORES)
