import sys
import os

import planetengine
disk = planetengine.disk
_built = planetengine._built
campaign = planetengine.campaign

JOBID = sys.argv[1]
path = os.path.dirname(__file__)

my_campaign = _built.load_built('campaign', path)

my_campaign._master_run(JOBID)
