import planetengine
from planetengine import functions as pfn
from planetengine.visualisation import QuickFig
from planetengine import analysis
from planetengine import _observer
from planetengine.utilities import message

def build(*args, name = None, **kwargs):
    built = Isobench(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Isobench(_observer.Observer):

    script = __file__
    name = 'isobench'

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

        keys = {'temperature', 'velocity'}
        obsVars = {key: system.obsVars[key] for key in keys}
        obsVars = pfn.convert(obsVars)

        temperature = obsVars['temperature']
        velocity = obsVars['velocity']

        saveVars = {'velocity': velocity}

        avTemp = pfn.integral.default(temperature)
        tempGrad = pfn.gradient.rad(temperature)
        Nu = pfn.integral.outer(tempGrad) / pfn.integral.inner(temperature) * -1.
        VRMS = pfn.operations.sqrt(
            pfn.integral.volume(
                pfn.operations.dot(
                    velocity,
                    velocity
                    )
                )
            )
        horizVel = pfn.component.ang(velocity)
        surfAngVel = pfn.integral.default(horizVel)

        statsDict = {
            'avTemp': avTemp,
            'Nu': Nu,
            'VRMS': VRMS,
            'surfAngVel': surfAngVel
            }

        formatDict = {
            'Nu': "{:.2f}",
            'avTemp': "{:.2f}",
            'VRMS': "{:.2f}",
            'surfAngVel': "{:.2f}",
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
            velocity
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
