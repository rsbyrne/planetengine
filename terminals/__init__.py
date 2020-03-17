from everest.builts._boolean import Boolean

class Terminal(Boolean):

    def __init__(self,
            **kwargs
            ):

        super().__init__(_bool_meta_fn = self._zone_meta_fn, **kwargs)

        self._pre_bool_fns.extend(self._pre_zone_fn)
        self._bool_fns.extend(self._zone_fn)
        self._post_bool_fns.extend(self._post_zone_fn)

    # Expect to be overwritten:
    def _pre_zone_fn(self):
        pass
    def _zone_fn(self):
        pass
    def _post_zone_fn(self):
        pass
    _zone_meta_fn = all
