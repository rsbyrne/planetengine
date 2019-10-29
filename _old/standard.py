# import underworld as uw
# from underworld import function as _fn
# import math
# import time
# import glucifer
# import numpy as np
# import math
# 
# from . import utilities
# from . import analysis
# from . import visualisation
# from .utilities import Grouper

# def build():

    ### HOUSEKEEPING: IMPORTANT! ###

#     inputs = locals().copy()
#     script = __file__
#     name = 'standard'
# #     hashID = utilities.hashstamp(script, inputs)
#
#     def attach(system):
#
#         step = system.step
#         modeltime = system.modeltime
#         if hasattr(system, 'obsVars'):
#             obsVars = [
#                 *sorted(system.varsOfState.items()),
#                 *[varTuple for varTuple in sorted(system.obsVars.items()) \
#                     if not varTuple in system.varsOfState.items()]
#                 ]
#         else:
#             obsVars = sorted(system.varsOfState.items())
#
#         ### MAKE STATS ###
#
#         statsDict = {}
#         formatDict = {}
#
#         for varName, var in obsVars:
#
#             pevar = standardise(var)
#             var = pevar.var
#
#             standardIntegralSuite = {
#                 'surface': ['volume', 'inner', 'outer'],
#                 'comp': [None, 'ang', 'rad'],
#                 'gradient': [None, 'ang', 'rad']
#                 }
#
#             for inputDict in suite.suite_list(standardIntegralSuite):
#
#                 try:
#
#                     anVar = analysis.Analyse.StandardIntegral(
#                         var,
#                         **inputDict
#                         )
#                     statsDict[varName + '_' + anVar.opTag] = anVar
#
#                     formatDict[varName + '_' + anVar.opTag] = "{:.2f}"
#
#                 except:
#                     pass
#
#         analyser = analysis.Analyser(
#             name,
#             statsDict,
#             formatDict,
#             step,
#             modeltime
#             )
#         analysers = [analyser,] # MAGIC NAME: MUST BE DEFINED
#
#         maincollector = analysis.DataCollector(analysers)
#         collectors = [maincollector,] # MAGIC NAME: MUST BE DEFINED
#
#         ### FIGS ###
#
#         fig = visualisation.QuickFig(
#             *obsVars,
#             figname = name,
#             colourBar = False
#             )
#         figs = [fig,] # MAGIC NAME: MUST BE DEFINED
#
#         return analysers, collectors, figs
#
#     ### HOUSEKEEPING: IMPORTANT! ###

    # return Grouper(locals())

# import underworld as uw
# from underworld import function as _fn
# import math
# import time
# import glucifer
# import numpy as np
# import math
#
# import planetengine
# from planetengine.utilities import Grouper
# from planetengine import analysis
# from planetengine import visualisation
#
# def build(obsVars, step, modeltime):
#
#     ### HOUSEKEEPING: IMPORTANT! ###
#
# #     inputs = locals().copy()
#     inputs = {'obsVars': sorted(obsVars.keys())}
#     script = __file__
#
#     ### MAKE STATS ###
#
#     statsDict = {}
#     formatDict = {}
#
#     for varName, var in sorted(obsVars.items()):
#
#         pevar = planetengine.standardise(var)
#         var = pevar.var
#
#         standardIntegralSuite = {
#             'surface': ['volume', 'inner', 'outer'],
#             'comp': ['mag', 'ang', 'rad'],
#             'gradient': [None, 'ang', 'rad']
#             }
#
#         for inputDict in planetengine.suite.suite_list(standardIntegralSuite):
#
#             anVar = analysis.Analyse.StandardIntegral(
#                 var,
#                 **inputDict
#                 )
#             statsDict[varName + '_' + anVar.opTag] = anVar
#
#             formatDict[varName + '_' + anVar.opTag] = "{:.2f}"
#
#     zerodAnalyser = analysis.Analyser(
#         'zerodData',
#         statsDict,
#         formatDict,
#         step,
#         modeltime
#         )
#     analysers = [zerodAnalyser,] # MAGIC NAME: MUST BE DEFINED
#
#     maincollector = analysis.DataCollector(analysers)
#     collectors = [maincollector,] # MAGIC NAME: MUST BE DEFINED
#
#     ### FIGS ###
#
#     mainfig = visualisation.QuickFig(
#         *sorted(obsVars.items()),
#         figname = 'standard'
#         )
#     figs = [mainfig,] # MAGIC NAME: MUST BE DEFINED
#
#     ### HOUSEKEEPING: IMPORTANT! ###
#
#     return Grouper(locals())
