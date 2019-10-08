import inspect
import os
import shutil
from . import utilities
from . import wordhash
from . import disk
from . import paths

from . import mpi
# from .utilities import check_reqs

def save_built(built, name, path):

    if mpi.rank == 0:
        if not os.path.isdir(path):
            os.makedirs(path)
        assert os.path.isdir(path)
    # mpi.barrier()

    inputs = built.inputs
    scripts = built.scripts

    disk.save_json(inputs, name, path)

    for index, script in enumerate(scripts):
        scriptName = name + '_' + str(index)
        disk.save_script(script, scriptName, path)

def save_builtsDir(builts, path, name = 'builts'):

    builtsDir = os.path.join(path, name)
    if mpi.rank == 0:
        if not os.path.isdir(builtsDir):
            os.makedirs(builtsDir)
        assert os.path.isdir(builtsDir)
    # mpi.barrier()

    for key, val in sorted(builts.items()):
        if type(val) == dict:
            subDir = 'sub_' + key
            save_builtsDir(val, builtsDir, name = subDir)
        else:
            val.save(builtsDir, name = key)

def load_built(name, path):

    inputDict = disk.load_json(name, path)

    index = 0

    scripts_to_load = []
    if mpi.rank == 0:
        while True:
            scriptName = name + '_' + str(index)
            scriptPath = os.path.join(
                path,
                scriptName
                ) + '.py'
            if os.path.isfile(scriptPath):
                scripts_to_load.append(scriptName)
                index += 1
            else:
                break
    scripts_to_load = mpi.comm.bcast(scripts_to_load, root = 0)
    # mpi.barrier()

    scriptModules = []
    for script_to_load in sorted(scripts_to_load):
        scriptModule = disk.load_script(script_to_load, path)
        scriptModules.append(scriptModule)

    built = scriptModules[0].build(
        *scriptModules[1:],
        **inputDict
        )

    built._post_load_hook(name, path)

    return built

def load_builtsDir(path, name = 'builts'):

    builtsDir = os.path.join(path, name)
    names = []
    dirs = []

    if mpi.rank == 0:
        assert os.path.isdir(builtsDir), \
            "Path " + builtsDir + " does not exist."
        files = os.listdir(builtsDir)
        for file in sorted(files):
            filePath = os.path.join(builtsDir, file)
            if os.path.isfile(filePath):
                if file.endswith('.json'):
                    builtName = os.path.splitext(
                        os.path.basename(file)
                        )[0]
                    names.append(builtName)
            elif os.path.isdir(filePath):
                if file[:4] == 'sub_':
                    dirs.append(file)
    names = mpi.comm.bcast(names, root = 0)
    dirs = mpi.comm.bcast(dirs, root = 0)
    # mpi.barrier()

    names = list(set(names))
    dirs = list(set(dirs))
    builts = {}
    for name in sorted(names):
        builts[name] = load_built(name, builtsDir)
    for subDir in sorted(dirs):
        subName = subDir[4:]
        builts[subName] = load_builtsDir(builtsDir, name = subDir)
    return builts

_accepted_inputTypes = {
    type([]),
    type(0),
    type(0.),
    type('0')
    }

def _clean_inputs(inputs):

    cleanVals = {
        'args',
        'kwargs',
        'self',
        '__class__'
        }
    for val in cleanVals:
        if val in inputs:
            del inputs[val]

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
        for key, val in sorted(builts.items()):
            if type(val) == dict:
                stamps[key] = make_stamps(val)
            elif isinstance(val, Built):
                stamps[key] = val.stamps
            else:
                raise Exception(
                    "Only Builts or dicts of builts can be stamped."
                    )
        allstamp = utilities.hashstamp(stamps)
        allwords = wordhash.wordhash(allstamp)
        stamps['all'] = [allstamp, allwords]
        return stamps

    else:

        toHash = {}
        if mpi.rank == 0:
            toHash['inputs'] = built.inputs
            toHash['scripts'] = [
                utilities.stringify(open(script)) \
                    for script in built.scripts
                ]
        toHash = mpi.comm.bcast(toHash, root = 0)
        # mpi.barrier()

        stamps = {
            key: utilities.hashstamp(val) \
                for key, val in sorted(toHash.items())
            }
        stamps['all'] = utilities.hashstamp(stamps)
        for stampKey, stampVal in stamps.items():
            stamps[stampKey] = [stampVal, wordhash.wordhash(stampVal)]

        return stamps

class Built:

    name = 'anon'

    def __init__(
            self,
            args, # subBuilts (as Builts)
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

    def _pre_save_hook(self, path, name = None):
        pass

    def _post_save_hook(self, path, name = None):
        pass

    def save(self, path = '', name = None):
        if name is None:
            name = self.name
        self._pre_save_hook(path, name)
        save_built(self, name, path)
        self._post_save_hook(path, name)

    def _post_load_hook(self, name, path):
        pass
