class Clip(_Function):
    # this function will take the input
    # and normalise it over an interval
    def __init__(self, inFn, lBnd, uBnd, *args, **kwargs):

        # Sanitising the inputs:

        _inFn = _Function.convert(inFn)
        if _inFn == None:
            raise ValueError( "Provided 'inFn' must a 'Function' or convertible type.")
        self._inFn = _inFn

        _lBnd = _Function.convert(lBnd)
        if _lBnd == None:
            raise ValueError( "Provided 'lBnd' must a 'Function' or convertible type.")
        self._lBnd = _lBnd

        _uBnd = _Function.convert(uBnd)
        if _uBnd == None:
            raise ValueError( "Provided 'uBnd' must a 'Function' or convertible type.")
        self._uBnd = _uBnd

        # Building the actual function:

        _clipFn = fn.branching.conditional([
            (self._inFn < self._lBnd, self._lBnd),
            (self._inFn > self._uBnd, self._uBnd),
            (True, self._inFn)
            ])
        self._clipFn = _clipFn

        # Setting the attribute for the underlying 'c' object:

        self._fncself = self._clipFn._fncself

        # Building the parent:

        super(Clip, self).__init__(argument_fns = [_inFn, _lBnd, _uBnd], **kwargs)
