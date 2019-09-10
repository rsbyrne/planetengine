from .utilities import check_reqs

class Built:

    _required_attributes{
        'inputs',
        'scripts',
        }

    def __init__(self):

        check_reqs(self)
