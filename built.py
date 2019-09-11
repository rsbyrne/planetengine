import inspect
import os
import shutil
import underworld as uw
from . import utilities
from . import wordhash
from . import disk
# from .utilities import check_reqs

def save_built(built, name, path):

    if uw.mpi.rank == 0:

        if not os.path.isdir(path):
            os.makedirs(path)

        inputs = built.inputs
        scripts = built.scripts

        disk.save_json(inputs, name, path)

        for index, script in enumerate(scripts):
            scriptName = name + '_' + str(index)
            disk.save_script(script, scriptName, path)

def save_builtsDir(builts, path):

    if uw.mpi.rank == 0:

        builtsDir = os.path.join(path, 'builts')
        if not os.path.isdir(builtsDir):
            os.makedirs(builtsDir)

        for builtName, built in sorted(builts.items()):
            built.save(builtsDir, name = builtName)

def load_built(name, path):

    inputDict = disk.load_json(name, path)
    scriptModules = []
    index = 0

    while True:
        scriptName = name + '_' + str(index)
        scriptPath = os.path.join(
            path,
            scriptName
            ) + '.py'
        fileCheck = False
        if uw.mpi.rank == 0:
            fileCheck = os.path.isfile(scriptPath)
        fileCheck = uw.mpi.comm.bcast(fileCheck, root = 0)
        if fileCheck:
            scriptModule = disk.load_script(scriptName, path)
            scriptModules.append(scriptModule)
            index += 1
        else:
            break

    built = scriptModules[0].build(
        *scriptModules[1:],
        **inputDict
        )

    return built

def load_builtsDir(path):
    builtsDir = os.path.join(path, 'builts')
    names = set()
    if uw.mpi.rank == 0:
        assert os.path.isdir(builtsDir)
        files = os.listdir(builtsDir)
        for file in os.listdir(builtsDir):
            if file.endswith('.json'):
                builtName = os.path.splitext(
                    os.path.basename(file)
                    )[0]
                names.add(builtName)
    names = uw.mpi.comm.bcast(names, root = 0)
    builts = {}
    for name in sorted(names):
        builts[name] = load_built(name, builtsDir)
    return builts

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

def make_stamps(built):

    stamps = {}

    if type(built) == dict:
        builts = built
        for builtName, built in builts.items():
            stamps[builtName] = built.stamps
        allstamp = utilities.hashstamp(stamps)
        allwords = wordhash.wordhash(allstamp)
        stamps['all'] = [allstamp, allwords]
        return stamps

    else:

        if uw.mpi.rank == 0:

            toHash = {}

            toHash['inputs'] = built.inputs
            toHash['scripts'] = [
                open(script) for script in built.scripts
                ]
            stamps = {
                key: utilities.hashstamp(val) \
                    for key, val in sorted(toHash.items())
                }
            stamps['all'] = utilities.hashstamp(stamps)
            for stampKey, stampVal in stamps.items():
                stamps[stampKey] = [stampVal, wordhash.wordhash(stampVal)]

        stamps = uw.mpi.comm.bcast(stamps, root = 0)

        return stamps

class Built:

    name = 'anon'

    def __init__(
            self,
            args,
            kwargs,
            inputs,
            script
            ):

        scripts = [script,]

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

        stamps = make_stamps(self)
        hashID = stamps['all'][1]

        self.stamps = stamps
        self.hashID = hashID

    def save(self, path, name = None):
        if name is None:
            name = self.name
        save_built(self, name, path)
