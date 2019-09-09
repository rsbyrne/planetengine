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
            assert not os.path.isfile(
                os.path.join(outputPath, 'stamps.json')
                )

    path = os.path.join(outputPath, instanceID)

    frame.expose_tar(path)

    builts = frame.load_builts(path)
    system = builts['system']
    initials = {
        key: val for key, val in builts.items() \
            if not key == 'system'
        }

    model = Model(
        system = system,
        initials = initials,
        outputPath = outputPath,
        instanceID = instanceID,
        _is_child = _is_child
        )

    return model

def make_model(
        system,
        initials,
        outputPath = None,
        instanceID = None,
        ):

    if outputPath is None:
        outputPath = paths.defaultPath

    builts = {'system': system, **initials}
    stamps = frame.make_stamps(builts)

    if instanceID is None:
        instanceID = 'pemod_' + stamps['all'][1]

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

    script = __file__

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

        builts = {'system': system, **initials}

        step = 0
        modeltime = 0.

        inFrames = []
        for IC in initials.values():
            try:
                inFrames.append(IC.inFrame)
            except:
                pass

        analysers = []
        collectors = []
        fig = QuickFig(
            system.varsOfState,
            # style = 'smallblack',
            )
        figs = [fig]
        saveVars = system.varsOfState

        # SPECIAL TO MODEL
        self.system = system
        self.observers = set()
        self.initials = initials
        self.analysers = analysers

        # NECESSARY FOR FRAME CLASS:
        self.outputPath = outputPath
        self.instanceID = instanceID
        self.inFrames = inFrames
        self.step = step
        self.modeltime = modeltime
        self.saveVars = saveVars
        self.figs = figs
        self.collectors = collectors
        self.builts = builts

        # OVERRIDE FRAME CLASS:
        self._autobackup = _autobackup
        self._autoarchive = _autoarchive
        self._is_child = _is_child
        self._parentFrame = _parentFrame

        super().__init__()

    # METHODS NECESSARY FOR FRAME CLASS:

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
        message("Initialisation complete!")

    def update(self):
        self.system.solve()

    # METHODS NOT NECESSARY:

    def _prompt_observers(self, prompt):
        observerList = utilities.parallelise_set(
            self.observers
            )
        for observer in observerList:
            observer.prompt(prompt)

    def _post_checkpoint_hook(self):
        self._prompt_observers('checkpointing')

    def all_analyse(self):
        message("Analysing...")
        for analyser in self.analysers:
            analyser.analyse()
        message("Analysis complete!")

    def report(self):
        message(
            '\n' \
            + 'Step: ' + str(self.step) \
            + ', modeltime: ' + '%.3g' % self.modeltime
            )
        for fig in self.figs:
            fig.show()

    def iterate(self):
        assert not self._is_child, \
            "Cannot iterate child models independently."
        message("Iterating step " + str(self.step) + " ...")
        dt = self.system.iterate()
        self.step += 1
        self.modeltime += dt
        self._prompt_observers('iterated')
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

        if not type(collectConditions) is list:
            collectConditions = [collectConditions,]
            assert len(collectConditions) == len(self.collectors)

        if checkpointCondition():
            self.checkpoint()

        message("Running...")

        while not stopCondition():

            try:
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

        message("Done!")
        if checkpointCondition():
            self.checkpoint()
