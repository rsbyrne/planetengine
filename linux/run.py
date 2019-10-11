import sys
import os
import json

from planetengine import _built

my_campaign = _built.load_built(
    'campaign',
    os.path.abspath(os.path.dirname(__file__))
    )

MODE = sys.argv[1] # single or auto
if MODE == 'single':
    JOBID = str(sys.argv[2])
    my_campaign._master_run(JOBID)
elif MODE == 'auto':
    CORES = int(sys.argv[2])
    my_campaign.autorun(cores = CORES)
elif MODE == 'multi':
    THREADS = int(sys.argv[2])
    CORES = int(sys.argv[3])
    my_campaign.multirun(threads = THREADS, cores = CORES)
else:
    raise Exception("'Mode' not recognised!")
