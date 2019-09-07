import sys
import os
import subprocess
workdir = '/home/jovyan/workspace'
if not workdir in sys.path:
    sys.path.append(workdir)
ignoreme = subprocess.call(['chmod', '-R', '777', workdir])
outdir = '/home/jovyan/workspace/out'
if not os.path.isdir(outdir):
    os.makedirs(outdir)
ignoreme = subprocess.call(['chmod', '-R', '777', outdir])

from . import utilities
from . import analysis
from . import checkpoint
from . import frame
from . import initials
from . import systems
from . import mapping
from . import shapes
from . import wordhash
from . import fieldops
from . import meshutils
from . import functions
from . import visualisation
from . import observer

from .utilities import message
from .utilities import log
from .fieldops import copyField
from .visualisation import quickShow
