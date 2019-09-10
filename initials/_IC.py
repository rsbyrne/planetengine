import underworld as uw
import numpy as np

from ..fieldops import copyField
from ..fieldops import set_scales
from ..fieldops import set_boundaries
from ..utilities import check_reqs
from ..generic import mesh2D as ICmesh
from .. import mapping

from types import ModuleType

class _IC:

    _required_attributes = {
        'script',
        'inputs',
        'varDim',
        'meshDim',
        'evaluate',
        }

    subICs = []

    def __init__(self):

        check_reqs(self)

        self.subICs = _construct_inners()

        scripts = [
            self.script,
            *[IC.script for IC in self.subICs]
            ]

        self.scripts = scripts
        self.nullVal = [1.] * self.varDim
        self.unitVal = [0.] * self.varDim

        self.var = ICmesh.add_variable(self.varDim)

        if hasattr(self, 'inVar'):
            tolerance = copyField(
                self.inVar,
                self.var,
                )
        else:
            boxDims = ((0., 1.),) * self.meshDim
            self.apply(self.var, boxDims)

    @staticmethod
    def _construct_inners(*args, **kwargs):

        subICs = []

        for arg in args:
            if isinstance(arg, _IC):
                subICs.append(arg)
            elif isinstance(arg, ModuleType):
                arg.build()
            else:
                raise Exception

    def copy(self, var, boxDims = None):

        tolerance = copyField(
            self.var,
            var,
            )

    def _get_ICdata(self, var, boxDims):

        if type(var) == uw.mesh.MeshVariable:
            box = mapping.box(var.mesh, var.mesh.data, boxDims)
        elif type(var) == uw.swarm.SwarmVariable:
            box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)

        ICdata = np.ones(var.data.shape)
        ICchain = [*self.subICs[-1::-1], self]

        for IC in ICchain:
            ICdata *= IC.evaluate(box)

        return ICdata

    def apply(self, var, boxDims = None):

        var.data[:] = self._get_ICdata(var, boxDims)

        if hasattr(var, 'scales'):
            set_scales(var, var.scales)

        if hasattr(var, 'bounds'):
            set_boundaries(var, var.bounds)
