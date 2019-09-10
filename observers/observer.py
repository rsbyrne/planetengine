from ..utilities import check_reqs
from ..builts import Built

class Observer(Built):

    _required_attributes{
        'inputs',
        'scripts',
        }

    def __init__(self):

        check_reqs(self)
