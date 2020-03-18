from everest.builts._boolean import Boolean
from ..utilities import _get_periodic_condition

class Final(Boolean):

    def __init__(self,
            check = True,
            **kwargs
            ):

        # Expects:
        # self.system

        self._zone_check = _get_periodic_condition(self.system, check)

        super().__init__(_bool_meta_fn = self._zone_meta_fn, **kwargs)

        self._pre_bool_fns.extend(self._master_pre_zone_fn)
        self._bool_fns.extend(self._master_zone_fn)
        self._post_bool_fns.extend(self._master_post_zone_fn)

    # Expect to be overwritten:
    _zone_meta_fn = all
    def _pre_zone_fn(self):
        pass
    def _zone_fn(self):
        pass
    def _post_zone_fn(self):
        pass

    def _master_pre_zone_fn(self):
        self._pre_zone_fn()
    def _master_zone_fn(self):
        if self._zone_check:
            return self._zone_fn()
        else:
            return False
    def _master_post_zone_fn(self):
        self._post_zone_fn()
