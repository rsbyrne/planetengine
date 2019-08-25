from . import _functions
from ._functions import get_planetVar
from ._functions import _construct
from functools import partial

convert = get_planetVar

raw = _functions

def _aliasmaker(
        outclassobj,
        inclassobj,
        argset = None,
        kwargname = None,
        ):
    if type(argset) == set:
        argset = {key: key for key in argset}
    if type(argset) == dict:
        for variantName, variant in argset.items():
            partialFn = partial(
                _construct,
                varClass = inclassobj,
                stringVariants = {
                    kwargname: variant
                    }
                )
            setattr(outclassobj, variantName, partialFn)
    else:
        raise Exception

def _multi_aliasmaker(outclassobj, mappingdict):
    for key, val in mappingdict.items():
        partialFn = partial(
            _construct,
            varClass = val,
            )
        setattr(outclassobj, key, partialFn)

class tidy:

    class basetypes:
        pass
    fns = {
        'constant': _functions.Constant,
        'variable': _functions.Variable,
        'shape': _functions.Shape,
        }
    _multi_aliasmaker(basetypes, fns)

    class utils:
        pass
    fns = {
        'projection': _functions.Projection,
        'substitute': _functions.Substitute,
        'binarise': _functions.Binarise,
        'booleanies': _functions.Booleanise,
        'handlenan': _functions.HandleNaN,
        'zeronan': _functions.ZeroNaN,
        }
    _multi_aliasmaker(utils, fns)

    class simple:

        class operations:
            pass
        argset = set(_functions.uwNamesToFns.keys())
        _aliasmaker(operations, _functions.Operations, argset, 'uwop')

        class component:
            pass
        argset = {'mag', 'rad', 'ang', 'ang1', 'ang2'}
        _aliasmaker(component, _functions.Component, argset, 'component')

        class gradient:
            pass
        argset = {'mag', 'rad', 'ang', 'ang1', 'ang2'}
        _aliasmaker(gradient, _functions.Gradient, argset, 'gradient')

        class comparison:
            pass
        argset = {'equals', 'notequals'}
        _aliasmaker(comparison, _functions.Comparison, argset, 'operation')

        class range:
            pass
        argset = {'in', 'out'}
        _aliasmaker(range, _functions.Range, argset, 'operation')

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
        _aliasmaker(integral, _functions.Integral, argset, 'surface')

        class quantile:
            pass
        argset = {
            'median': 2,
            'tercile': 3,
            'quartile': 4,
            'quintile': 5,
            'sextile': 6,
            'septile': 7,
            'octile': 8,
            'nonile': 9,
            'decile': 10,
            'duodecile': 12,
            'hexadecile': 16,
            'vigintile': 20,
            'percentile': 100,
            }
        _aliasmaker(
            quantile,
            _functions.Quantile,
            argset,
            'ntiles'
            )
        # for alias in argset:
        #     aliasobj = getattr(quantile, alias)
        #     subargset = {
        #         key: val for key, val \
        #         in zip(
        #             [str(i) for i in range(argset[alias])],
        #             [i for i in range(argset[alias])]
        #             )
        #         }
        #     _aliasmaker(
        #         aliasobj,
        #         _functions.Quantile,
        #         subargset,
        #         'nthtile'
        #         )

    fns = {
        'clip': _functions.Clip,
        'interval': _functions.Interval,
        'region': _functions.Region,
        }
    _multi_aliasmaker(simple, fns)
