from everest.builts._boolean import Boolean
from everest.builts._state import State
from ..utilities import _get_periodic_condition

class Final(Boolean, State):

    def __init__(self,
            check = True,
            **kwargs
            ):

        # Expects:
        # self.system

        self._zone_check = _get_periodic_condition(self.system, check)
        self.initialised = False

        # State attributes:
        self._state_stampee = self.system

        super().__init__(
            supertype = 'Final',
            _bool_meta_fn = self._zone_meta_fn,
            **kwargs
            )

        # Boolean attributes:
        # self._pre_bool_fns.append(self._master_pre_zone_fn)
        self._bool_fns.append(self._master_zone_fn)
        # self._post_bool_fns.append(self._master_post_zone_fn)

    # Expect to be overwritten:
    _zone_meta_fn = all
    def _zone_initialise(self):
        pass
    def _pre_zone_fn(self):
        pass
    def _zone_fn(self):
        pass
    def _post_zone_fn(self):
        pass
    def _zone_finalise(self):
        pass

    def _master_zone_initialise(self):
        self._zone_initialise()
        self.initialised = True
    def _master_pre_zone_fn(self):
        return self._pre_zone_fn()
    def _master_zone_fn(self):
        if not self.initialised:
            self._master_zone_initialise()
        self._master_pre_zone_fn()
        if self._zone_check:
            self._state_stamp()
            boolOut = self._zone_fn()
        else:
            boolOut = False
        self._master_post_zone_fn()
        if boolOut:
            self._master_zone_finalise()
        return boolOut
    def _master_post_zone_fn(self):
        return self._post_zone_fn()
    def _master_zone_finalise(self):
        self._zone_finalise()
        self.initialised = False

from .flat import Flat
from .averages import Averages
