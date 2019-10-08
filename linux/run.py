import sys
import os

import planetengine
disk = planetengine.disk
_built = planetengine._built
campaign = planetengine.campaign

JOBID = sys.argv[1]
path = os.path.dirname(__file__)

my_campaign = _built.load_built('campaign', path)

job = disk.load_json(JOBID, my_campaign.fm.directories['jobs']['available']['.'])

my_campaign.run(job)
