import underworld as uw
import numpy as np

from .fieldops import copyField
from .fieldops import set_scales
from .fieldops import set_boundaries
from .utilities import check_reqs
from .generic import mesh2D as ICmesh
from . import mapping
from ._built import Built

from types import ModuleType

class IC(Built):

    _required_attributes = {
        'evaluate',
        }

    def __init__(
            self,
            args,
            kwargs,
            inputs,
            script
            ):

        check_reqs(self)

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = script
            )

    def _get_ICdata(self, var, boxDims):

        if type(var) == uw.mesh.MeshVariable:
            box = mapping.box(var.mesh, var.mesh.data, boxDims)
        elif type(var) == uw.swarm.SwarmVariable:
            box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)

        ICdata = np.ones(var.data.shape)
        ICchain = [*self.subs[-1::-1], self]

        for IC in ICchain:
            ICdata *= IC.evaluate(box)

        return ICdata

    def _apply(self, var, boxDims = None):

        var.data[:] = self._get_ICdata(var, boxDims)

    def apply(self, var, boxDims = None):

        self._apply(var, boxDims = boxDims)

        if hasattr(var, 'scales'):
            set_scales(var, var.scales)

        if hasattr(var, 'bounds'):
            set_boundaries(var, var.bounds)
