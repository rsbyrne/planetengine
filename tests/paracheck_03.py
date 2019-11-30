import os
from timeit import timeit
import random

import planetengine
import everest

with everest.paths.TestDir() as outputPath:

    system = planetengine.systems.isovisc.build(res = 16)
    system.anchor(path = outputPath)
    observer = planetengine.observers.standard.build(system)
    system.co_anchor(observer)

    # print('!' * 100)
    # print(system.hashID)
    # print('!' * 100)

    def testfn():
        system.store()
        system.save()
        observer.store()
        observer.save()
        for i in range(3):
            for i in range(3):
                for i in range(3):
                    system.go(3)
                system.store()
                observer.store()
            system.save()
            observer.save()
        system.load(9)
        system.iterate()
        system.store()
        system.save()
        observer.store()
        observer.save()
        for i in range(3):
            for i in range(3):
                for i in range(3):
                    system.go(3)
                system.store()
                observer.store()
            system.save()
            observer.save()
        system_loaded = everest.built.load(
            system.hashID,
            system.hashID,
            outputPath
            )
        system_loaded.load(10)
        system_loaded.iterate()
        system_loaded.store()
        system_loaded.save()
        observer.store()
        observer.save()
        for i in range(3):
            for i in range(3):
                for i in range(3):
                    system_loaded.go(3)
                system_loaded.store()
                observer.store()
            system_loaded.save()
            observer.save()

    system.show()

    timing = timeit(testfn, number = 1)
    planetengine.message(timing)
    planetengine.message(system.counts_captured)
    planetengine.message(observer.counts_captured)
