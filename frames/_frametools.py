import underworld as uw
import tarfile
import os
import shutil
import json
import copy
import glob

from .. import paths
from .. import utilities
from .. import disk
from ..wordhash import wordhash as wordhashFn
from .. import checkpoint
from ..utilities import message
from ..utilities import check_reqs
from ..visualisation import QuickFig

from . import model as model_module
from . import observer as observer_module

frameTypes = {
    'model': model_module,
    'observer': observer_module,
    }
prefixDict = {
    'model': 'pemod',
    'observer': 'peobs',
    }

def expose_tar(path):

    tarpath = path + '.tar.gz'

    print(path)

    if uw.mpi.rank == 0:
        assert os.path.isdir(path) or os.path.isfile(tarpath), \
            "No model found at that directory!"

    if uw.mpi.rank == 0:
        if os.path.isfile(tarpath):
            assert not os.path.isdir(path), \
                "Conflicting archive and directory found."
            message("Tar found - unarchiving...")
            with tarfile.open(tarpath) as tar:
                tar.extractall(path)
            message("Unarchived.")
            assert os.path.isdir(path), \
                "Archive contained the wrong model file somehow."
            os.remove(tarpath)

def load_json(jsonName, path):
    filename = jsonName + '.json'
    jsonDict = {}
    if uw.mpi.rank == 0:
        with open(os.path.join(path, filename)) as json_file:
            jsonDict = json.load(json_file)
    jsonDict = uw.mpi.comm.bcast(jsonDict, root = 0)
    return jsonDict

load_inputs = load_json

def load_builts(path):
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
        inputDict = load_json(name, builtsDir)
        scriptModules = []
        index = 0
        while True:
            scriptName = name + '_' + str(index) + '.py'
            scriptPath = os.path.join(
                builtsDir,
                scriptName
                )
            fileCheck = False
            if uw.mpi.rank == 0:
                fileCheck = os.path.isfile(scriptPath)
            fileCheck = uw.mpi.comm.bcast(fileCheck, root = 0)
            if fileCheck:
                scriptModule = utilities.local_import(
                    scriptPath
                    )
                scriptModules.append(scriptModule)
                index += 1
            else:
                break
        built = scriptModule.build(
            *scriptModules[1:],
            **inputDict
            )
        builts[name] = built
    return builts

def make_stamps(builts):
    scripts = {}
    inputs = {}
    for builtName, built in sorted(builts.items()):
        scripts[builtName] = built.scripts
        inputs[builtName] = built.inputs
    assert inputs.keys() == scripts.keys()
    stamps = {}
    if uw.mpi.rank == 0:
        toHash = {}
        for key in sorted(inputs.keys()):
            inputList = inputs[key]
            scriptList = scripts[key]
            toHash[key + 'inputs'] = inputList
            toHash[key + 'scripts'] = [
                open(script) for script in scriptList
                ]
        stamps = {
            key: utilities.hashstamp(val) \
                for key, val in sorted(toHash.items())
            }
        stamps['all'] = utilities.hashstamp(stamps)
        for stampKey, stampVal in stamps.items():
            stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
    stamps = uw.mpi.comm.bcast(stamps, root = 0)
    return stamps

def make_frame(
        frameType,
        builts,
        outputPath = None,
        instanceID = None,
        ):

    if outputPath is None:
        outputPath = paths.defaultPath

    stamps = make_stamps(builts)

    if instanceID is None:
        prefix = prefixDict[frameType]
        instanceID = prefix + '_' + stamps['all'][1]

    path = os.path.join(outputPath, instanceID)
    tarpath = path + '.tar.gz'

    directory_state = ''

    if uw.mpi.rank == 0:

        if os.path.isdir(path):
            if os.path.isfile(tarpath):
                raise Exception(
                    "Cannot combine model directory and tar yet."
                    )
            else:
                directory_state = 'directory'
        elif os.path.isfile(tarpath):
            directory_state = 'tar'
        else:
            directory_state = 'clean'

    directory_state = uw.mpi.comm.bcast(directory_state, root = 0)

    if directory_state == 'tar':
        if uw.mpi.rank == 0:
            with tarfile.open(tarpath) as tar:
                tar.extract('stamps.json', path)
            with open(os.path.join(path, 'stamps.json')) as json_file:
                loadstamps = json.load(json_file)
            shutil.rmtree(path)
            assert loadstamps == stamps

    if not directory_state == 'clean':
        message("Preexisting model found! Loading...")
        frame = load_frame(
            outputPath,
            instanceID
            )
    else:
        frameModule = frameTypes[frameType]
        message("Making a new frame...")
        frame = frameModule.build(
            builts,
            outputPath = outputPath,
            instanceID = instanceID
            )

    return frame

def load_frame(
        outputPath = None,
        instanceID = '',
        loadStep = 0,
        _is_child = False,
        ):
    '''
    Creates a new 'model' instance attached to a pre-existing
    model directory. LoadStep can be an integer corresponding
    to a previous checkpoint step, or can be the string 'max'
    which loads the highest stable checkpoint available.
    '''

    if outputPath is None:
        outputPath = paths.defaultPath

    # Check that target directory is not inside
    # another planetengine directory:

    if not _is_child:
        if uw.mpi.rank == 0:
            assert not os.path.isfile(
                os.path.join(outputPath, 'stamps.json')
                )

    path = os.path.join(outputPath, instanceID)

    expose_tar(path)

    builts = load_builts(path)

    info = load_json('info', path)

    frameType = info['frameType']
    frameModule = frameTypes[frameType]

    frame = frameModule.build(
        builts,
        outputPath = outputPath,
        instanceID = instanceID,
        _is_child = _is_child
        )

    return frame

# def load_system(path):
#     builtsDir = os.path.join(path, 'builts')
#     params = frame.load_inputs('system', builtsDir)
#     systemscript = utilities.local_import(os.path.join(builtsDir, 'system_0.py'))
#     system = systemscript.build(**params['system_0'])
#     return system, params

# def load_initials(system, path):
#     builtsDir = os.path.join(path, 'builts')
#     configs = frame.load_inputs('initial', builtsDir)
#     initials = {}
#     for varName in sorted(system.varsOfState):
#         initials[varName] = {**configs[varName]}
#         initialsLoadName = varName + '_0.py'
#         module = utilities.local_import(
#             os.path.join(builtsDir, initialsLoadName)
#             )
#         # check if an identical 'initial' object already exists:
#         if hasattr(module, 'LOADTYPE'):
#             initials[varName] = initialModule.load.build(
#                 **configs[varName], _outputPath = path, _is_child = True
#                 )
#         elif module.IC in [type(IC) for IC in initials.values()]:
#             for priorVarName, IC in sorted(initials.items()):
#                 if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
#                     initials[varName] = initials[priorVarName]
#                     break
#         else:
#             initials[varName] = module.build(
#                 **configs[varName]
#                 )
        # if module.IC in [type(IC) for IC in initials.values()]:
        #     for priorVarName, IC in sorted(initials.items()):
        #         if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
        #             initials[varName] = initials[priorVarName]
        #             break
        # else:
        #     initials[varName] = module.build(
        #         **configs[varName]
        #         )
    # return initials, configs
