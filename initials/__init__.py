import underworld as uw

from everest.builts._applier import Applier

from ..fieldops import set_scales
from ..fieldops import set_boundaries
from .. import mapping

from types import ModuleType

class Configuration(Applier):

    _swapscript = '''from planetengine.initials import Configuration as CLASS'''

    def __init__(self,
            **channels
            ):

        for key, val in sorted(channels.items()):
            if not isinstance(val, Applier):
                raise TypeError

        self.channels = channels

        super().__init__()

        self._apply_fns.append(self._configuration_apply_fn)

    def _configuration_apply_fn(self, obj, mapping = {}):
        for key, val in sorted(self.channels.items()):
            try: toKey = mapping[key]
            except KeyError: toKey = key
            var = obj.locals[toKey]
            val.apply(var)

class Channel(Applier):

    def __init__(self,
            **kwargs
            ):

        # Expects:
        # self.evaluate

        super().__init__(**kwargs)

        self._apply_fns.append(self._channel_apply_fn)

    def _channel_get_data(self, var, boxDims):
        if type(var) == uw.mesh.MeshVariable:
            box = mapping.box(var.mesh, var.mesh.data, boxDims)
        elif type(var) == uw.swarm.SwarmVariable:
            box = mapping.box(var.swarm.mesh, var.swarm.data, boxDims)
        channeldata = self.evaluate(box)
        return channeldata

    def _channel_apply_fn(self, var, boxDims = None):
        if hasattr(var, 'data'):
            var.data[:] = self._channel_get_data(var, boxDims)
        elif hasattr(var, 'value'):
            var.value = self.evaluate()
        else:
            raise TypeError
        if hasattr(var, 'scales'):
            set_scales(var, var.scales)
        if hasattr(var, 'bounds'):
            set_boundaries(var, var.bounds)

from .constant import Constant
from .sinusoidal import Sinusoidal
from .copy import Copy
from .extents import Extents
