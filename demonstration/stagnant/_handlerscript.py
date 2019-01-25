import underworld as uw
from underworld import function as fn
import math
import time
import glucifer
import numpy as np
import math
import planetengine
from planetengine import InitialConditions
from planetengine import Analysis
from planetengine import Grouper

def build():

    ### HOUSEKEEPING: IMPORTANT! ###

    inputs = locals().copy()
    script = __file__

    ### FIGURES ###

    def make_figs(system):
        fig = glucifer.Figure(edgecolour = "white", quality = 2)
        figTempComponent = fig.Surface(
            system.mesh, system.temperatureField,
            colourBar = True
            )
        figVelComponent = fig.VectorArrows(
            system.mesh, system.velocityField
            )
        figViscComponent = fig.Contours(
            system.mesh, fn.math.log10(system.viscosityFn),
            colours = "red black", interval = 0.5, colourBar = False 
            )

        figs = {'fig': fig, }
        return figs

    ### DATA ###

    def make_data(system):
        zerodDataDict = {
            'Nu': Analysis.Analyse.DimensionlessGradient(system.temperatureField, system.mesh,
                surfIndexSet = system.outer, baseIndexSet = system.inner
                ),
            'avTemp': Analysis.Analyse.ScalarFieldAverage(system.temperatureField, system.mesh),
            'VRMS': Analysis.Analyse.VectorFieldVolRMS(system.velocityField, system.mesh),
            'surfVRMS': Analysis.Analyse.VectorFieldSurfRMS(
                system.velocityField, system.mesh, system.outer
                ),
            'avVisc': Analysis.Analyse.ScalarFieldAverage(system.viscosityFn, system.mesh),
            'yielding': Analysis.Analyse.ScalarFieldAverage(
                fn.branching.conditional([(system.creepViscFn < system.plasticViscFn, 0.), (True, 1.)]),
                system.mesh
                ),
            'step': Analysis.Analyse.ArrayStripper(system.step, (0, 0)),
            'modeltime': Analysis.Analyse.ArrayStripper(system.modeltime, (0, 0)),
            }

        zerodFormatDict = {
            'Nu': "{:.1f}",
            'avTemp': "{:.2f}",
            'VRMS': "{:.2f}",
            'surfVRMS': "{:.2f}",
            'avVisc': "{:.1E}",
            'yielding': "{0:.0%}",
            'step': "{:.0f}",
            'modeltime': "{:.1E}",
            }

        zerodAnalyser = Analysis.Analyser('zerodData', zerodDataDict, zerodFormatDict)
        dataCollector = Analysis.DataCollector([zerodAnalyser,])
        data = {
            'analysers': [zerodAnalyser,],
            'dataCollectors': [dataCollector,],
            }
        return Grouper(data)

    ### HOUSEKEEPING: IMPORTANT! ###
    return Grouper(locals())
