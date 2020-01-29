import os
from timeit import timeit
import random

import planetengine
import everest

with planetengine.paths.TestDir() as outputPath:

    system = planetengine.systems.isovisc.get(res = 16)
    system.anchor(path = outputPath)
    observer = planetengine.observers.standard.get(system)
    observer.coanchor(system)

    system.store()
    system.save()
    observer.store()
    observer.save()
    for i in range(2):
        for i in range(3):
            system.go(3)
            system.store()
            observer.store()
        system.save()
        observer.save()
    for i in range(3):
        system.go(3)
        system.store()
        observer.store()
    system.save()
    observer.save()

    # for i in range(1):
    #     for i in range(1):
    #         for i in range(3):
    #             system.go(3)
    #         system.store()
    #         observer.store()
    #         observer.store()
    #     system.save()
        # observer.save()
    # system.load(9)
    # system.iterate()
    # system.store()
    # system.save()
    # observer.store()
    # observer.save()
    # for i in range(3):
    #     for i in range(3):
    #         for i in range(3):
    #             system.go(3)
    #         system.store()
    #         observer.store()
    #     system.save()
    #     observer.save()
