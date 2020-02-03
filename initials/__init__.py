import underworld as uw

from everest.builts._applier import Applier

from ..fieldops import set_scales
from ..fieldops import set_boundaries
from .. import mapping

from types import ModuleType

class IC(Applier):

    def __init__(
            self,
            evaluate,
            initialise = lambda: None,
            **kwargs
            ):

        def _get_ICdata(var, boxDims):

            if type(var) == uw.mesh.MeshVariable:
                box = mapping.box(var.mesh, var.mesh.data, boxDims)
            elif type(var) == uw.swarm.SwarmVariable:
                box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)
            ICdata = evaluate(box)

            return ICdata

        def _apply(var, boxDims = None):

            if hasattr(var, 'data'):
                var.data[:] = _get_ICdata(var, boxDims)
            elif hasattr(var, 'value'):
                var.value = evaluate()
            else:
                raise TypeError

        def apply(var, boxDims = None):

            initialise()

            _apply(var, boxDims = boxDims)

            if hasattr(var, 'scales'):
                set_scales(var, var.scales)

            if hasattr(var, 'bounds'):
                set_boundaries(var, var.bounds)

        super().__init__(**kwargs)

        self._apply_fns.append(apply)
