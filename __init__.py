import os
planetengineDir = os.path.abspath(os.path.dirname(__file__))

from . import utilities
from . import analysis
from . import system
from . import IC
from . import initials
from . import systems
from . import observers
from . import mapping
from . import shapes
from . import fieldops
from . import meshutils
from . import functions
from . import visualisation
from . import tests
from . import paths
from . import suite

from .utilities import message
from .utilities import log
from .fieldops import copyField
quickShow = visualisation.quickShow
