from .. import initials
from .. import systems
from .. import functions as pfn
from ..visualisation import quickShow
import numpy as np
from timeit import timeit
from . import testsystems

def testfn():

    system = testsystems.get_system()
    ICs = system.initials

    variable1 = pfn.convert(system.velocityField, 'velocity')
    variable2 = pfn.convert(system.temperatureField, 'temperature')
    constant = pfn.convert(2.)
    shape = pfn.convert(np.array([[0.2, 0.1], [0.9, 0.3], [0.8, 0.7], [0.4, 0.9]]))
    vanilla = pfn.convert(system.viscosityFn, 'viscosity')

    def makevar():
        var = variable2
        var = var ** constant
        var = pfn.Region(var, shape)
        var = var * variable1
        var = pfn.Component.rad(var)
        var = pfn.Gradient.mag(var)
        var = pfn.HandleNaN.zero(var)
        var = var + 1.
        var = var * vanilla
        var = pfn.Quantiles.terciles(var)
        var = pfn.Substitute(var, 2., 20.)
        var = pfn.Binarise(var)
        var = var * variable1
        var_a, var_b = pfn.Split.getall(var)
        var_b = var_b ** -1
        var = pfn.Merge(var_a, var_b)
        var = pfn.Component.rad(var)
        var = pfn.Gradient.ang(var)
        var = pfn.Normalise(var, [1., 2.])
        var = pfn.Clip.torange(var, [1.2, 1.8])
        var = pfn.HandleNaN(var, 1.6)
        var = pfn.Filter(var, 1.6)
        var = pfn.Region(var, shape)
        var = pfn.HandleNaN.zero(var)
        var = pfn.Binarise(var)
        return var

    print(round(timeit(makevar, number = 3) / 3, 3))

    var = makevar()

    quickShow(var.mesh, var)

    def testfn(var, timings = '', layer = 1):
        def outer_timefn(var, timinglist = []):
            system.reset()
            var.update()
            system.iterate()
            timing = timeit(var.update, number = 1)
            timinglist.append(timing)
            return timinglist
        var_timings = []
        for i in range(3):
            var_timings = outer_timefn(var, var_timings)
        var_timing = sum(var_timings) / len(var_timings)
        var_timing = round(var_timing, 6)
        timings += '\n'
        newrow = ''
        newrow += layer * '-' + ' '
        newrow += var.opTag
        newrow += ': '
        newrow += '.' * (56 - len(newrow)) + ' '
        newrow += str(var_timing)
        timings += newrow
        for inVar in var.inVars:
            timings = testfn(inVar, timings, layer + 1)
        return timings

    timings = testfn(var)

    print(timings)

    red = pfn.Integral(var)

    system.reset()
    red.update()
    system.iterate()
    print(red.evaluate())
    print(red.evaluate())
    system.iterate()
    print(red.evaluate())
    print(red.evaluate())

    def testfn():
        freshsteps = []
        stalesteps = []
        for i in range(3):
            system.reset()
            red.update
            system.iterate()
            freshsteps.append(timeit(red.update, number = 1))
        for i in range(3):
            stalesteps.append(timeit(red.update, number = 1))
        average_fresh = round(sum(freshsteps) / len(freshsteps), 5)
        average_stale = round(sum(stalesteps) / len(stalesteps), 5)
        ratio = round(average_fresh / average_stale, 5)
        return(average_fresh, average_stale, ratio)

    print(testfn())
