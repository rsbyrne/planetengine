from everest.builts import Built

class Mesh(Built):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

from .annulus import Annulus
