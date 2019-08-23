from . import _functions
from ._functions import get_planetVar
from functools import partial

convert = get_planetVar

raw = _functions

def _aliasmaker(outclassobj, inclassobj, argset):
    for variant in argset:
        partialfn = partial(
            inclassobj,
            variant = variant,
            )
        setattr(outclassobj, variant, partialfn)

class tidy:

    class basetypes:

        constant = _functions.Constant
        variable = _functions.Variable

    class utils:

        projection = _functions.Projection
        substitute = _functions.Substitute
        binarise = _functions.Binarise
        booleanies = _functions.Booleanise
        handleNaN = _functions.HandleNaN

    class simple:

        clip = _functions.Clip
        interval = _functions.Interval

        class operations:
            pass
        argset = set(_functions.uwNamesToFns.keys())
        _aliasmaker(operations, _functions.Operations, argset)

        class component:
            pass
        argset = {'mag', 'rad', 'ang', 'ang1', 'ang2'}
        _aliasmaker(component, _functions.Component, argset)

        class gradient:
            pass
        argset = {'mag', 'rad', 'ang', 'ang1', 'ang2'}
        _aliasmaker(gradient, _functions.Gradient, argset)

        class comparison:
            pass
        argset = {'equals', 'notequals'}
        _aliasmaker(comparison, _functions.Comparison, argset)

        class range:
            pass
        argset = {'in', 'out'}
        _aliasmaker(range, _functions.Range, argset)

        class integral:
            pass
        argset = {
            'volume',
            'inner',
            'outer',
            'left',
            'right',
            'front',
            'back'
            }
        _aliasmaker(integral, _functions.Integral, argset)

    class advanced:

        quantile = _functions.Quantile
        region = _functions.Region
