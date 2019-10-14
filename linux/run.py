import sys
import os
import json

from planetengine import campaign

my_campaign = campaign.load(
    os.path.basename(os.path.dirname(__file__)),
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

MODE = sys.argv[1] # single or auto
if MODE == 'single':
    try: JOBID = str(sys.argv[2])
    except: JOBID = None
    my_campaign._master_run(JOBID)
elif MODE == 'auto':
    try: CORES = int(sys.argv[2])
    except: CORES = 1
    my_campaign.autorun(cores = CORES)
else:
    raise Exception("'Mode' not recognised!")
