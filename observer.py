import underworld as uw
from underworld import function as fn
import math
import time
import glucifer
import numpy as np
import math

from . import utilities
from . import analysis
from . import visualisation
from .utilities import Grouper
from .standards import standardise

def build(obsVars, step, modeltime):

    ### HOUSEKEEPING: IMPORTANT! ###

#     inputs = locals().copy()
    inputs = {'obsVars': sorted(obsVars.keys())}
    script = __file__

    ### MAKE STATS ###

    statsDict = {}
    formatDict = {}

    for varName, var in sorted(obsVars.items()):

        pevar = standardise(var)
        var = pevar.var

        standardIntegralSuite = {
            'surface': ['volume', 'inner', 'outer'],
            'comp': ['mag', 'ang', 'rad'],
            'gradient': [None, 'ang', 'rad']
            }

        for inputDict in utilities.suite_list(standardIntegralSuite):

            anVar = analysis.Analyse.StandardIntegral(
                var,
                **inputDict
                )
            statsDict[varName + '_' + anVar.opTag] = anVar

            formatDict[varName + '_' + anVar.opTag] = "{:.2f}"

    zerodAnalyser = analysis.Analyser(
        'zerodData',
        statsDict,
        formatDict,
        step,
        modeltime
        )
    analysers = [zerodAnalyser,] # MAGIC NAME: MUST BE DEFINED

    maincollector = analysis.DataCollector(analysers)
    collectors = [maincollector,] # MAGIC NAME: MUST BE DEFINED

    ### FIGS ###

    mainfig = visualisation.QuickFig(
        *sorted(obsVars.items()),
        figname = 'standard'
        )
    figs = [mainfig,] # MAGIC NAME: MUST BE DEFINED

#     ### REPORT ###

#     reportfig = mainfig
#     reportanalyser = zerodAnalyser

    ### HOUSEKEEPING: IMPORTANT! ###

    return Grouper(locals())