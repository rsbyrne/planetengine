import numpy as np

from underworld import function as fn
UWFn = fn._function.Function

from . import _planetvar
from . import _basetypes
from . import vanilla
from ._construct import _construct
from .. import utilities
message = utilities.message

def _convert(var, varName = None):

    if isinstance(var, _planetvar.PlanetVar):
        # message("Already a _planetvar.PlanetVar! Returning.")
        return var

    if hasattr(var, '_planetVar'):
        outVar  = var._planetVar()
        if isinstance(outVar, _planetvar.PlanetVar):
            if (outVar.stringVariants['varName'] == varName) \
                    or (varName is None):
                return outVar

    if type(var) == np.ndarray:
        if len(var.shape) == 2:
            if varName is None:
                varName = _basetypes.Shape.defaultName
            stringVariants = {'varName': varName}
            varClass = _basetypes.Shape
        elif len(var.shape) == 1:
            valString = utilities.stringify(var)
            stringVariants = {'val': valString}
            varClass = _basetypes.Constant
        else:
            raise Exception

    else:
        var = UWFn.convert(var)
        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) == 0:
            # hence is a constant!
            valString = utilities.stringify(
                var.evaluate()[0]
                )
            stringVariants = {'val': valString}
            varClass = _basetypes.Constant
        elif type(var) in _basetypes.Variable.convertTypes:
            if varName is None:
                varName = _basetypes.Variable.defaultName
            stringVariants = {'varName': varName}
            varClass = _basetypes.Variable
        elif isinstance(var, UWFn):
            if not varName is None:
                stringVariants = {'varName': varName}
                varClass = _basetypes.Variable
            else:
                stringVariants = {}
                varClass = vanilla.Vanilla
        else:
            raise Exception

    var = _construct(
        varClass,
        var,
        **stringVariants
        )

    return var

def convert(*args):
    if len(args) == 1:
        arg = args[0]
        if type(arg) == dict:
            converted = _dict_convert(arg)
        # elif type(arg) == list:
        #     converted = convert(*arg, _return_type = 'list')
        # elif type(arg) == tuple:
        #     converted = convert(*arg, _return_type = 'tuple')
        elif type(arg) == tuple:
            converted = tuple([convert(subArg) for subArg in arg])
        else:
            converted = _convert(arg)
    elif len(args) == 2:
        if type(args[0]) == str:
            converted = _convert(args[1], args[0])
        elif type(args[1]) == str:
            converted = _convert(args[0], args[1])
        else:
            converted = tuple([convert(arg) for arg in args])
    else:
        converted = tuple([convert(arg) for arg in args])
    return converted

get_planetVar = convert

def _dict_convert(inDict):
    all_converted = {}
    for varName, var in sorted(inDict.items()):
        newVar = _convert(var, varName)
        all_converted[varName] = newVar
    return all_converted
