__all__ = [
    'utilities',
    'analysis',
    'initials',
    'systems',
    'observers',
    'mapping',
    'shapes',
    'fieldops',
    'meshutils',
    'functions',
    'visualisation',
    # 'paths'
    ]

import os
planetengineDir = os.path.abspath(os.path.dirname(__file__))

from everest import \
    Reader, Writer, Fetch, Scope, set_global_anchor, load, mpi, disk

from . import systems
from . import observers
from . import initials
from . import visualisation
vis = visualisation
from . import functions
from . import analysis

from .utilities import message
from .visualisation import quickShow
