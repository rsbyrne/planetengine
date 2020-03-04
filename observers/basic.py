from underworld import function as fn

from everest import mpi

from planetengine.observers import Observer
from planetengine.functions import integral, gradient, operations, component
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

        temp = observee.locals[tempKey]
        cond = observee.locals[condKey]
        radGrad = gradient.rad(temp)
        surfInt = integral.outer(radGrad)
        radGradRef = gradient.rad(cond)
        surfIntRef = integral.outer(radGradRef)
        Nu = surfInt / surfIntRef
        analysers['Nu'] = self.Nu = Nu
        theta = temp - cond
        avTemp = integral.volume(temp)
        avTheta = integral.volume(theta)
        analysers['avTheta'] = self.avTheta = avTheta

        vel = observee.locals[velKey]
        VRMS = operations.sqrt(integral.volume(component.sq(vel)))
        analysers['VRMS'] = self.VRMS = VRMS
        # angVel = component.ang(vel)
        # surfVel = integral.outer(angVel)

        if viscKey in observee.locals.__dict__:
            visc = observee.locals[viscKey]
            avVisc = integral.volume(visc)
            analysers['avVisc'] = self.avVisc = avVisc

        rasterArgs = []
        rasterArgs.append(theta)
        if plasticViscKey in observee.locals.__dict__:
            plastic = observee.locals[plasticViscKey]
            logInvPlastic = operations.log(1. / plastic)
            self.yielding = yielding = plastic < visc
            yieldFrac = integral.volume(yielding)
            analysers['yielding'] = self.yieldFrac = yieldFrac
            rasterArgs.append(logInvPlastic)
        if viscKey in observee.locals.__dict__:
            stress = visc * vel
            logMagStress = operations.log(component.mag(stress))
            rasterArgs.append(logMagStress)
        else:
            velMag = component.mag(vel)
            rasterArgs.append(velMag)
        raster = Raster(*rasterArgs)
        analysers['raster'] = self.raster = raster

        self.observee, self.analysers = observee, analysers

        self.baselines = {
            'condTemp': integral.volume(cond).evaluate()
            }

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
