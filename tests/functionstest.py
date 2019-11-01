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

    system = testsystems.get_system(res = 16, Ra = 1e4)

    variable1 = pfn.convert(system.velocityField, 'velocity')
    variable2 = pfn.convert(system.temperatureField, 'temperature')
    constant = pfn.convert(2.)
    shape = pfn.convert(np.array([[0.2, 0.1], [0.9, 0.3], [0.8, 0.7], [0.4, 0.9]]))
    vanilla = pfn.convert(system.viscosityFn, 'viscosity')

    makeFns = [
        lambda var: var ** constant,
        lambda var: pfn.region.default(var, shape),
        lambda var: var * variable1,
        lambda var: pfn.component.rad(var),
        lambda var: pfn.operations.log(var),
        lambda var: pfn.gradient.mag(var),
        lambda var: pfn.handlenan.zeroes(var),
        lambda var: pfn.binarise.default(var),
        lambda var: var + 1.,
        lambda var: var * vanilla,
        lambda var: pfn.quantiles.terciles(var),
        lambda var: pfn.substitute.default(var, 2., 0.),
        lambda var: var * variable1,
        lambda var: pfn.merge.default(*[
            compVar * -1. \
                for compVar in pfn.split.getall(var)
            ]),
        lambda var: pfn.component.rad(var),
        lambda var: pfn.gradient.ang(var),
        lambda var: pfn.normalise.default(var, [1., 2.]),
        lambda var: pfn.clip.torange(var, [1.2, 1.8]),
        lambda var: pfn.handlenan.default(var, 1.6),
        lambda var: pfn.filter.default(var, 1.6),
        lambda var: pfn.region.default(var, shape),
        lambda var: pfn.handlenan.zeroes(var),
        lambda var: pfn.binarise.default(var)
        ]

    var = variable2
    timings = []
    for makeFn in makeFns:
        timing = timeit(lambda: makeFn(var), number = 1) / 1.
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
        for i in range(1):
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

    red = pfn.integral._construct(var)

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
        for i in range(1):
            system.reset()
            red.update
            system.iterate()
            freshsteps.append(timeit(red.update, number = 1))
        for i in range(1):
            stalesteps.append(timeit(red.update, number = 1))
        average_fresh = round(sum(freshsteps) / len(freshsteps), 5)
        average_stale = round(sum(stalesteps) / len(stalesteps), 5)
        ratio = round(average_fresh / average_stale, 5)
        return(average_fresh, average_stale, ratio)

    output = testfn()
    message(output)
