import os
from timeit import timeit
import random

import planetengine
import everest

with planetengine.paths.TestDir() as outputPath:

    system = planetengine.systems.isovisc.build(res = 16)
    system.anchor(path = outputPath)

    def testfn():
        for i in range(3):
            for i in range(3):
                system.go(3)
                system.store()
        system.save()
        system.load(9)
        system.iterate()
        system.store()
        system.save()
        system_loaded = everest.built.load(
            system.hashID,
            system.hashID,
            outputPath
            )
        system_loaded.load(15)
        system_loaded.iterate()
        system_loaded.store()
        system_loaded.save()
        system.load(27)
        system.iterate()
        system.store()
        system.save()

    timing = timeit(testfn, number = 1)
    planetengine.message(timing)
    planetengine.message(system.counts_captured)
