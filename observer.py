# from .utilities import check_reqs
# from .utilities import hashstamp
# from .wordhash import wordhash as wordhashFn
# from .frame import _Frame
# from .frame import _scripts_and_stamps
# from . import checkpoint
#
# import os
#
# import underworld as uw
#
# class Observer(_Frame):
#
#     _required_attributes = {
#         'system', # system
#         'initials', # dict
#         'outputPath', # str
#         'scripts', # list of str
#         'inputs', # list of dict
#         'figs', # list of glucifer figs
#         'collectors', # list of collectors
#         'obsVars', # dict
#         }
#
#     def __init__(self):
#
#         check_reqs(self)
#
#         scripts = {}
#         for index, script in enumerate(self.scripts):
#             scriptname = 'observerscript_' + str(index)
#             scripts[scriptname] = script
#
#         inputs = {}
#         for index, inputDict in enumerate(inputs):
#             inputName = 'observerinputs_' + str(index)
#             inputs[inputName] = inputDict
#
#         # Making stamps and stuff
#
#         _model_inputs, _model_stamps, _model_scripts = \
#             _scripts_and_stamps(self.system, self.initials)
#
#         inHashID = 'pemod_' + _model_stamps['all'][1]
#
#         stamps = {}
#         if uw.mpi.rank == 0:
#             stamps = {
#                 'inputs': hashstamp(self.inputs),
#                 'scripts': hashstamp(
#                     [open(script) for scriptname, script \
#                         in sorted(scripts.items())]
#                     ),
#                 'inHash': _model_stamps['all'][0]
#                 }
#             stamps['all'] = hashstamp(stamps)
#             for stampKey, stampVal in stamps.items():
#                 stamps[stampKey] = [stampVal, wordhashFn(stampVal)]
#         stamps = uw.mpi.comm.bcast(stamps, root = 0)
#         stamps['inStamps'] = _model_stamps
#
#         scripts.update(_model_scripts)
#         inputs.update(_model_inputs)
#
#         instanceID = 'peobs_' + stamps['all'][1]
#
#         # checkpointer = checkpoint.Checkpointer(
#         #     stamps = stamps,
#         #     saveVars = self.obsVars,
#         #     step = self.system.step,
#         #     modeltime = self.system.modeltime,
#         #     figs = self.figs,
#         #     dataCollectors = self.collectors,
#         #     scripts = scripts,
#         #     inputs = inputs,
#         #     )
#
#         self.checkpointer = checkpointer
#
#         self.instanceID = instanceID
#         self.stamps = stamps
#         self.scripts = scripts
#         self.inputs = inputs
#
#         self.path = os.path.join(self.outputPath, self.instanceID)
#
#         self.step = 0
#         self.modeltime = 0.
#
#         self.inFrames = []
#         self._is_child = False
#         self._autoarchive = True
#
#         'system', # must be a 'system'-like object
#         'initials', # must be dict (key = str, val = IC)
#         'outputPath', # must be str
#         'instanceID', # must be str
#         '_is_child', # must be bool
#         'inFrames', # must be list of Frames objects
#         '_autoarchive', # must be bool
#         'checkpoint', # must take pos arg (path)
#         'load_checkpoint', # must take pos arg (step)
#         'stamps', # must be dict
#         'step', # must be int
#
#         super().__init__()
#
#     # def update(self):
#     #     self.step = self.system.step.value
#     #     self.modeltime = self.system.modeltime.value
#
#     def checkpoint(self, path = None):
#         if path is None:
#             path = self.path
#         self.checkpointer.checkpoint(path)
#
#     def load_checkpoint(self, path):
#         pass
