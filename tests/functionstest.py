from .. import initials
from .. import systems
from .. import functions as pfn
from ..visualisation import quickShow
from ..utilities import message
import numpy as np
import math
from timeit import timeit
from . import testsystems

def testfn():

    system = testsystems.get_system(Ra = 1e4, res = 32)

    variable1 = pfn.convert(system.velocityField, 'velocity')
    variable2 = pfn.convert(system.temperatureField, 'temperature')
    constant = pfn.convert(2.)
    shape = pfn.convert(np.array([[0.2, 0.1], [0.9, 0.3], [0.8, 0.7], [0.4, 0.9]]))
    vanilla = pfn.convert(system.viscosityFn, 'viscosity')

    makeFns = [
        lambda var: var ** constant,
        lambda var: pfn.Region(var, shape),
        lambda var: var * variable1,
        lambda var: pfn.Component.rad(var),
        lambda var: pfn.Operations.log(var),
        lambda var: pfn.Gradient.mag(var),
        lambda var: pfn.HandleNaN.zeroes(var),
        lambda var: var + 1.,
        lambda var: var * vanilla,
        lambda var: pfn.Quantiles.terciles(var),
        lambda var: pfn.Substitute(var, 2., 0.),
        lambda var: pfn.Binarise(var),
        lambda var: var * variable1,
        lambda var: pfn.Merge(*[
            compVar * -1. \
                for compVar in pfn.Split.getall(var)
            ]),
        lambda var: pfn.Component.rad(var),
        lambda var: pfn.Gradient.ang(var),
        lambda var: pfn.Normalise(var, [1., 2.]),
        lambda var: pfn.Clip.torange(var, [1.2, 1.8]),
        lambda var: pfn.HandleNaN(var, 1.6),
        lambda var: pfn.Filter(var, 1.6),
        lambda var: pfn.Region(var, shape),
        lambda var: pfn.HandleNaN.zeroes(var),
        lambda var: pfn.Binarise(var)
        ]

    var = variable2
    timings = []
    for makeFn in makeFns:
        timing = timeit(lambda: makeFn(var), number = 3) / 3.
        timings.append(timing)
        var = makeFn(var)
        message(var.opTag, round(timing, 3))
    message("All together: ", round(sum(timings), 3))
    quickShow(var)

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

    message(timings)

    red = pfn.Integral(var)

    system.reset()
    red.update()
    system.iterate()
    val = red.evaluate()
    message(val)
    val = red.evaluate()
    message(val)
    system.iterate()
    val = red.evaluate()
    message(val)
    val = red.evaluate()
    message(val)

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

    output = testfn()
    message(output)
