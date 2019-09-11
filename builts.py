import inspect
# from .utilities import check_reqs

_accepted_inputTypes = {
    type([]),
    type(0),
    type(0.),
    type('0')
    }

def _clean_inputs(inputs):

    del inputs['args']
    del inputs['kwargs']
    del inputs['self']
    del inputs['__class__']

    for key, val in inputs.items():
        if type(val) == tuple:
            inputs[key] = list(val)
        if not type(val) in _accepted_inputTypes:
            raise Exception(
                "Type " + str(type(val)) + " not accepted."
                )

def _check_kwargs(kwargs):
    for kwarg in kwargs:
        if not _check_key(kwarg):
            raise Exception(
                "Kwarg " + str(kwarg) + " not accepted. \
                Only kwargs of form 'sub0', 'sub1' etc. accepted."
                )

def _check_key(key):
    check1 = key[:4] == '_sub'
    check2 = True
    try: int(key[4:])
    except: check2 = False
    return all([check1, check2])

def _check_args(args):
    try:
        assert all([isinstance(arg, Built) for arg in args])
        return "allbuilts"
    except:
        assert all([inspect.ismodule(arg) for arg in args])
        return "allmodules"

class Built:

    def __init__(
            self,
            args,
            kwargs,
            inputs,
            scripts
            ):

        _clean_inputs(inputs)
        argsType = _check_args(args)
        _check_kwargs(kwargs)

        subs = []

        if argsType == 'allbuilts':
            subs = args
        else:
            argIndex = 0
            for subName, subKwargs in sorted(kwargs.items()):
                subModule = args[argIndex]
                subsubNo = len([
                    key for key in subKwargs if _check_key(key)
                    ])
                subArgs = args[argIndex + 1: argIndex + 1 + subsubNo]
                sub = subModule.build(*subArgs, **subKwargs)
                subs.append(sub)
                argIndex += 1 + subsubNo
        for index, sub in enumerate(subs):
            subName = '_sub' + str(index)
            inputs[subName] = sub.inputs
            scripts.extend(sub.scripts)

        self.subs = subs
        self.kwargs = kwargs
        self.inputs = inputs
        self.scripts = scripts
