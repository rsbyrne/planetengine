import planetengine
from planetengine import functions as pfn
from planetengine.visualisation import QuickFig
from planetengine import analysis
from planetengine import _observer
from planetengine.utilities import message

def build(*args, name = None, **kwargs):
    built = Standard(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Standard(_observer.Observer):

    script = __file__
    name = 'standard'

    def __init__(
            self,
            *args,
            **kwargs
            ):

        inputs = locals().copy()

        super().__init__(
            args,
            kwargs,
            inputs,
            self.script,
            self._attach,
            self._prompt
            )

    def _attach(self, system):

        varDict = {}

        keys = {'temperature', 'velocity', 'stress'}
        obsVars = {key: system.obsVars[key] for key in keys}
        obsVars = pfn.convert(obsVars)


        temperature = obsVars['temperature']
        velocity = obsVars['velocity']
        stress = obsVars['stress']

        saveVars = {'velocity': velocity, 'stress': stress}

        stressMag = pfn.component.mag(stress)
        avStress = pfn.integral.default(stressMag)
        avTemp = pfn.integral.default(temperature)
        tempGrad = pfn.gradient.rad(temperature)
        Nu = pfn.integral.outer(tempGrad) / pfn.integral.inner(temperature) * -1.
        velMag = pfn.component.mag(velocity)
        VRMS = pfn.integral.default(velMag)
        horizVel = pfn.component.ang(velocity)
        surfVRMS = pfn.integral.default(horizVel)

        statsDict = {
            'avStress': avStress,
            'avTemp': avTemp,
            'Nu': Nu,
            'VRMS': VRMS,
            'surfVRMS': surfVRMS
            }

        formatDict = {
            'Nu': "{:.2f}",
            'avTemp': "{:.2f}",
            'VRMS': "{:.2f}",
            'surfVRMS': "{:.2f}",
            'avStress': "{:.2f}"
            }

        mainAnalyser = analysis.Analyser(
            'standard',
            statsDict,
            formatDict,
            system.step,
            system.modeltime
            )
        mainCollector = analysis.DataCollector([mainAnalyser,])

        saveCollectors = [mainCollector,]

        mainFig = QuickFig(
            temperature,
            velocity,
            stressMag,
            style = 'smallblack'
            )

        saveFigs = [mainFig]

        self.mainAnalyser = mainAnalyser
        self.mainCollector = mainCollector
        self.mainFig = mainFig

        return saveVars, saveFigs, saveCollectors

    def _prompt(self):
        if self.step() % 10 == 0:
            message("Observer collecting...")
            self.mainCollector.collect()
            message("Observer collected.")

    def report(self):
        self.mainAnalyser.report()
        self.mainFig.show()
