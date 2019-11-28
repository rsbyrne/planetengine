import planetengine
from timeit import timeit
system1 = planetengine.systems.isovisc.build(res = 16, f = 0.5, aspect = 2.)
var1 = system1.obsVars['temperature']
system2 = planetengine.systems.isovisc.build(res = 32, f = 1., aspect = 1)
var2 = system2.obsVars['temperature']
def testfn():
    tolerance = planetengine.fieldops.copyField(var1**2, var2)
planetengine.message(timeit(testfn, system2.reset, number = 10) / 10.)
planetengine.quickShow(var2)
