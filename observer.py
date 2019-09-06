# from .utilities import Grouper
# from .utilities import hashstamp
# from .wordhash import wordhash as wordhashFn
# from .checkpoint import Checkpointer
# from .frame import _scripts_and_stamps
# from .frame import _Frame
# import underworld as uw
# #
# def make_observer_stamps_inputs(system, initials, options):
#     stamps = {}
#     _model_inputs, _model_stamps, _model_scripts = \
#         _scripts_and_stamps(system, initials)
#     if uw.mpi.rank == 0:
#         stamps.update(_model_stamps)
#         stamps = {
#             'options': hashstamp(options),
#             'scripts': hashstamp(
#                 [open(script) for scriptname, script \
#                     in sorted(scripts.items())]
#                 )
#             }
#         stamps['allstamp'] = hashstamp(stamps)
#         for stampKey, stampVal in stamps.items():
#             stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
#     stamps = uw.mpi.comm.bcast(stamps, root = 0)
#     return stamps
#
# class Observer(_Frame):
#
#     figs = []
#     collectors = []
#
#     def __init__(
#             self,
#             system,
#             initials,
#             obsInps = {},
#             subObservers = [],
#             outputPath = '',
#             _autoarchive = True,
#             _parentFrame = None,
#             _is_child = False,
#             _autobackup = True,
#             ):
#
#         scripts = {}
#         for index, subObserver in enumerate(subObservers):
#             scriptname = 'observerscript_' + str(index)
#             scripts[scriptname] = script
#
#         # Making stamps and stuff
#
#         _model_inputs, _model_stamps, _model_scripts = \
#             _scripts_and_stamps(system, initials)
#
#         self.inHashID = 'pemod_' + _model_stamps['allstamp'][1]
#
#         stamps = {}
#         if uw.mpi.rank == 0:
#             stamps = {
#                 'obsInps': hashstamp(obsInps),
#                 'scripts': hashstamp(
#                     [open(script) for scriptname, script \
#                         in sorted(scripts.items())]
#                     )
#                 }
#         #     stamps['allstamp'] = hashstamp(stamps)
#         #     for stampKey, stampVal in stamps.items():
#         #         stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
#         # stamps = uw.mpi.comm.bcast(stamps, root = 0)
#
#         # Making the checkpointer:
#
#         checkpointer = Checkpointer(
#             stamps = stamps,
#             step = system.step,
#             modeltime = system.modeltime,
#             figs = self.figs,
#             dataCollectors = self.collectors,
#             scripts = scripts,
#             inputs = {'obsInps': obsInps}
#             )
#
#         self.checkpointer = checkpointer
#         self.inputs = inputs
#         self.scripts = scripts
#         self.stamps = stamps
#         self.system = system
#         self.initials = initials
#         self.step = system.step
#         self.modeltime = system.modeltime
#         self.instanceID = stamps['allstamp'][1]
#         self.outputPath = outputPath
#
#         super().__init__()
#
#     def prompt(self):
#         pass
#
#     def checkpoint(self, path):
#         self.checkpointer.checkpoint(path)
#
#     def load_checkpoint(self, path):
#         pass
