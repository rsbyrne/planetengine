from underworld import function as fn

from everest import mpi

from planetengine.observers import Observer
from planetengine.functions import \
    integral, gradient, operations, component, getstat, comparison
from planetengine.visualisation.raster import Raster
from planetengine.visualisation.quickfig import QuickFig

class Basic(Observer):

    def __init__(self,
            observee,
            tempKey = 'temperatureField',
            condKey = 'conductionField',
            velKey = 'velocityField',
            viscKey = 'viscosityFn',
            plasticViscKey = 'plasticViscFn',
            **kwargs
            ):

        analysers = dict()
        baselines = dict()
        rasterArgs = []

        temp = observee.locals[tempKey]
        cond = observee.locals[condKey]
        baselines['condTemp'] = integral.volume(cond).evaluate()
        adiabatic = gradient.rad(temp)
        conductive = gradient.rad(cond)
        self.Nus = Nus = adiabatic / conductive
        Nu = integral.outer(Nus)
        analysers['Nu'] = self.Nu = Nu
        # surfInt = integral.outer(radGrad)
        # surfIntRef = integral.outer(radGradRef)
        # Nu = surfInt / surfIntRef

        theta = temp - cond
        avTemp = integral.volume(temp)
        avTheta = integral.volume(theta)
        analysers['theta_av'] = self.avTheta = avTheta
        analysers['theta_min'] = getstat.mins(theta)
        analysers['theta_range'] = getstat.ranges(theta)
        rasterArgs.append(theta)

        vel = observee.locals[velKey]
        velMag = component.mag(vel)
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = self.VRMS = VRMS
        analysers['velMag_range'] = getstat.ranges(velMag)
        # angVel = component.ang(vel)
        # surfVel = integral.outer(angVel)

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            avVisc = integral.volume(visc)
            analysers['visc_av'] = self.avVisc = avVisc
            minVisc, maxVisc = getstat.mins(visc), getstat.maxs(visc)
            baselines['visc_min'] = minVisc.evaluate()
            baselines['visc_max'] = maxVisc.evaluate()
        if plasticViscKey in observee.locals.__dict__:
            plastic = observee.locals[plasticViscKey]
            yielding = comparison.isequal(visc, plastic)
            yieldFrac = integral.volume(yielding)
            analysers['yieldFrac'] = self.yieldFrac = yieldFrac
            logInvPlastic = operations.log(1. / plastic)
            analysers['logInvPlastic_av'] = integral.volume(logInvPlastic)
            analysers['logInvPlastic_min'] = getstat.mins(logInvPlastic)
            analysers['logInvPlastic_range'] = getstat.ranges(logInvPlastic)
            rasterArgs.append(logInvPlastic)
        if viscKey in observee.locals.__dict__:
            stress = visc * vel
            logMagStress = operations.log(component.mag(stress))
            analysers['logMagStress_av'] = integral.volume(logMagStress)
            analysers['logMagStress_min'] = getstat.mins(logMagStress)
            analysers['logMagStress_range'] = getstat.ranges(logMagStress)
            rasterArgs.append(logMagStress)
        else:
            velMag = component.mag(vel)
            rasterArgs.append(velMag)
        raster = Raster(*rasterArgs)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        self.baselines = baselines

        visVars = [temp, vel]
        try: visVars.append(visc)
        except NameError: pass
        self.fig = QuickFig(*visVars)

        super().__init__(baselines = self.baselines, **kwargs)

        self.set_freq(10)

    def show(self):
        self.fig.show()

    def report(self):
        outs = self.out()
        outkeys = self.outkeys
        def dot_aligned(seq):
            snums = [str(n) for n in seq]
            dots = [len(s.split('.', 1)[0]) for s in snums]
            m = max(dots)
            return [' '*(m - d) + s for s, d in zip(snums, dots)]
        names, datas = [], []
        for name, data in zip(outkeys, outs):
            if data.shape == ():
                if name == 'count':
                    val = str(int(data))
                else:
                    val = "{:.2f}".format(data)
                justname = name.ljust(max([len(key) for key in outkeys]))
                names.append(justname)
                datas.append(val)
        datas = dot_aligned(datas)
        outlist = [name + ' : ' + data for name, data in zip(names, datas)]
        outstr = '\n'.join(outlist)
        mpi.message(outstr)

CLASS = Basic
