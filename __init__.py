import os
planetengineDir = os.path.abspath(os.path.dirname(__file__))

from . import utilities
from . import analysis
from . import initials
from . import systems
from . import observers
from . import mapping
from . import shapes
from . import fieldops
from . import meshutils
from . import functions
from . import visualisation
from . import paths

from .utilities import message
quickShow = visualisation.quickShow
