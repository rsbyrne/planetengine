import underworld as uw
import tarfile
import os
import shutil
import json
import copy
import glob

from . import paths
from . import utilities
from . import disk
from .wordhash import wordhash as wordhashFn
from . import checkpoint
from . import initials as initialModule
from .utilities import message
from .utilities import check_reqs
from .visualisation import QuickFig

from . import frame

def load_system(path):
    builtsDir = os.path.join(path, 'builts')
    params = frame.load_inputs('system', builtsDir)
    systemscript = utilities.local_import(os.path.join(builtsDir, 'system_0.py'))
    system = systemscript.build(**params['system_0'])
    return system, params

def load_initials(system, path):
    builtsDir = os.path.join(path, 'builts')
    configs = frame.load_inputs('initial', builtsDir)
    initials = {}
    for varName in sorted(system.varsOfState):
        initials[varName] = {**configs[varName]}
        initialsLoadName = varName + '_0.py'
        module = utilities.local_import(
            os.path.join(builtsDir, initialsLoadName)
            )
        # check if an identical 'initial' object already exists:
        if hasattr(module, 'LOADTYPE'):
            initials[varName] = initialModule.load.build(
                **configs[varName], _outputPath = path, _is_child = True
                )
        elif module.IC in [type(IC) for IC in initials.values()]:
            for priorVarName, IC in sorted(initials.items()):
                if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
                    initials[varName] = initials[priorVarName]
                    break
        else:
            initials[varName] = module.build(
                **configs[varName]
                )
        # if module.IC in [type(IC) for IC in initials.values()]:
        #     for priorVarName, IC in sorted(initials.items()):
        #         if type(IC) == module.IC and configs[varName] == configs[priorVarName]:
        #             initials[varName] = initials[priorVarName]
        #             break
        # else:
        #     initials[varName] = module.build(
        #         **configs[varName]
        #         )
    return initials, configs

def load_model(
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
            assert not os.path.isfile(os.path.join(outputPath, 'stamps.json')), \
                "Loading a child model as an independent frame \
                not currently supported."

    path = os.path.join(outputPath, instanceID)

    frame.expose_tar(path)

    builts = frame.load_builts({'system'})
    system = builts['system']

    # system, params = load_system(path)

    initials, configs = load_initials(system, path)

    model = Model(
        system = system,
        initials = initials,
        outputPath = outputPath,
        instanceID = instanceID,
        _is_child = _is_child
        )

    # we may know it's a child already,
    # but we may not have constructed the parent yet.

    # If it's a loaded frame, it must have been saved to disk at some point -
    # hence its internal frames will all be held as copies inside
    # the loaded frame. We need to flag this:
    for inFrame in model.inFrames:
        inFrame._parentFrame = model

    model.checkpoints = frame.find_checkpoints(path, model.stamps)

    model.load_checkpoint(loadStep)

    if all([
            model._autoarchive,
            not model.archived,
            not _is_child
            ]):
        model.archive()

    return model

# def _make_stamps(
#         params,
#         systemscripts,
#         configs,
#         initialscripts
#         ):
#
#     message("Making stamps...")
#
#     stamps = {}
#     if uw.mpi.rank == 0:
#         stamps = {
#             'params': utilities.hashstamp(params),
#             'systemscripts': utilities.hashstamp(
#                 [open(script) for script in systemscripts]
#                 ),
#             'configs': utilities.hashstamp(configs),
#             'initialscripts': utilities.hashstamp(
#                 [open(script) for script in initialscripts]
#                 )
#             }
#         stamps['allstamp'] = utilities.hashstamp(
#             [val for key, val in sorted(stamps.items())]
#             )
#         stamps['system'] = utilities.hashstamp(
#             (stamps['params'], stamps['systemscripts'])
#             )
#         stamps['initials'] = utilities.hashstamp(
#             (stamps['configs'], stamps['initialscripts'])
#             )
#         for stampKey, stampVal in stamps.items():
#             stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
#     stamps = uw.mpi.comm.bcast(stamps, root = 0)
#
#     message("Stamps made.")
#
#     return stamps

def _make_stamps(inputs, scripts):
    assert inputs.keys() == scripts.keys()
    stamps = {}
    if uw.mpi.rank == 0:
        toHash = {}
        for key in sorted(inputs.keys()):
            inputList = inputs[key]
            scriptList = scripts[key]
            stamps[key + 'inputs'] = inputList
            stamps[key + 'scripts'] = [
                [open(script) for script in initialscripts]
                ]
        stamps = {
            key, utilitie.hashstamp(val) \
                for key, val in sorted(toHash.items())
            }
    stamps = uw.mpi.comm.bcast(stamps, root = 0)
    return stamps

def _scripts_and_stamps(
        system,
        initials,
        ):

    scripts = {}
    inputs = {}

    scripts['system'] = system.scripts

    params = []
    for index, paramsDict in enumerate(system.params):
        params.append(paramsDict)
    inputs['system'] = params

    allconfigs = {}
    initialscripts = []
    for varName, IC in sorted(initials.items()):
        configs = []
        for index, script in enumerate(IC.scripts):
            scriptname = varName + '_' + str(index)
            scripts[scriptname] = script
            initialscripts.append(script)
        configs.append(IC.inputs)
        allconfigs[varName] = configs
        inputs[varName] = configs

    assert inputs.keys() == scripts.keys()

    stamps = _make_stamps(
        inputs,
        scripts
        )

    return inputs, stamps, scripts

def make_model(
        system,
        initials,
        outputPath = None,
        instanceID = None,
        ):

    if outputPath is None:
        outputPath = paths.defaultPath

    inputs, stamps, scripts = \
        _scripts_and_stamps(system, initials)

    if instanceID is None:
        instanceID = 'pemod_' + stamps['allstamp'][1]

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

    if directory_state == 'clean':
        message("Making a new model...")
        model = Model(
            system,
            initials,
            outputPath,
            instanceID
            )

    else:
        message("Preexisting model found! Loading...")
        model = load_model(
            outputPath,
            instanceID
            )

    return model

class Model(frame.Frame):

    def __init__(self,
            system,
            initials,
            outputPath = None,
            instanceID = 'test',
            _autoarchive = True,
            _parentFrame = None,
            _is_child = False,
            _autobackup = True,
            ):

        if outputPath is None:
            outputPath = paths.defaultPath

        assert system.varsOfState.keys() == initials.keys()

        message("Building model...")

        self.system = system
        self.observers = []
        self.initials = initials
        self.outputPath = outputPath
        self.instanceID = instanceID
        self._autoarchive = _autoarchive
        self._parentFrame = _parentFrame
        self._is_child = _is_child
        self._autobackup = _autobackup

        inputs, stamps, scripts = \
            _scripts_and_stamps(system, initials)

        self.inputs = inputs
        self.stamps = stamps
        self.scripts = scripts

        self.hashID = 'pemod_' + self.stamps['allstamp'][1]

        self.varsOfState = self.system.varsOfState
        self.step = 0
        self.modeltime = 0.

        self.inFrames = []
        for IC in self.initials.values():
            try:
                self.inFrames.append(IC.inFrame)
            except:
                pass

        self.analysers = []
        self.collectors = []
        self.fig = QuickFig(
            system.varsOfState,
            style = 'smallblack',
            )
        self.figs = [self.fig]
        self.saveVars = self.system.varsOfState

        self.subCheckpointFns = [
            observer.checkpoint \
                for observer in self.observers
            ]

        super().__init__()

    def initialise(self):
        message("Initialising...")
        initialModule.apply(
            self.initials,
            self.system,
            )
        self.system.solve()
        self.step = 0
        self.modeltime = 0.
        self.update()
        self.status = "ready"
        message("Initialisation complete!")

    def all_analyse(self):
        message("Analysing...")
        for analyser in self.analysers:
            analyser.analyse()
        message("Analysis complete!")

    def update(self, solve = True):
        # self.step = self.system.step.value
        # self.modeltime = self.system.modeltime.value
        if solve:
            self.system.solve()
        for observer in self.observers:
            observer.prompt()

    def report(self):
        message(
            '\n' \
            + 'Step: ' + str(self.step) \
            + ', modeltime: ' + '%.3g' % self.modeltime
            )
        self.fig.show()

    def iterate(self):
        assert not self._is_child, \
            "Cannot iterate child models independently."
        message("Iterating step " + str(self.step) + " ...")
        dt = self.system.iterate()
        self.step += 1
        self.modeltime += dt
        self.update(solve = False)
        message("Iteration complete!")

    def go(self, steps):
        stopStep = self.step + steps
        self.traverse(lambda: self.step >= stopStep)

    def traverse(self, stopCondition,
            collectConditions = lambda: False,
            checkpointCondition = lambda: False,
            reportCondition = lambda: False,
            forge_on = False,
            ):

        self.status = "pre-traverse"

        if not type(collectConditions) is list:
            collectConditions = [collectConditions,]
            assert len(collectConditions) == len(self.collectors)

        if checkpointCondition():
            self.checkpoint()

        message("Running...")

        while not stopCondition():

            try:
                self.status = "traversing"
                self.iterate()
                if checkpointCondition():
                    self.checkpoint()
                else:
                    for collector, collectCondition in zip(
                            self.collectors,
                            collectConditions
                            ):
                        if collectCondition():
                            collector.collect()
                if reportCondition():
                    self.report()

            except:
                if forge_on:
                    message("Something went wrong...loading last checkpoint.")
                    assert type(self.most_recent_checkpoint) == int, "No most recent checkpoint logged."
                    self.load_checkpoint(self.most_recent_checkpoint)
                else:
                    raise Exception("Something went wrong.")

        self.status = "post-traverse"
        message("Done!")
        if checkpointCondition():
            self.checkpoint()
        self.status = "ready"

# An example of a custom class that inherits from _Frame:
# class CustomFrame(Model):
#     def __init__(self):
#
#         system = planetengine.systems.arrhenius.build(res = 16)
#         initials = {'temperatureField': planetengine.initials.sinusoidal.build(freq = 1.)}
#         planetengine.initials.apply(
#             initials,
#             system,
#             )
#         system.solve()
#
#         self.system = system
#         self.initials = initials
#         self.outputPath = '/home/jovyan/workspace/data/test'
#         self.instanceID = 'testFrame'
#         self.stamps = {'a': 1}
#         self.step = 0
#         self._is_child = False
#         self.inFrames = []
#         self._autoarchive = True
#         checkpointer = checkpoint.Checkpointer(
#             stamps = self.stamps,
#             step = system.step,
#             modeltime = system.modeltime,
#             )
#         mypath = os.path.join(self.outputPath, self.instanceID)
#         def checkpoint(path = None):
#             if path is None:
#                 path = mypath
#             checkpointer.checkpoint(path)
#         self.checkpoint = checkpoint
#         def load_checkpoint(step):
#             pass
#         self.load_checkpoint = load_checkpoint
#
#         super().__init__()
