import sys
import os
import subprocess
workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)
ignoreme = subprocess.call(['chmod', '-R', '777', workPath])
outPath = '/home/jovyan/workspace/out'
if not os.path.isdir(outPath):
    os.makedirs(outPath)
ignoreme = subprocess.call(['chmod', '-R', '777', outPath])
testPath = '/home/jovyan/workspace/out/test'

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
from . import tests
from . import disk

from .utilities import message
from .utilities import log
from .fieldops import copyField
from .visualisation import quickShow
