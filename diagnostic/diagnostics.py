import sys
sys.path.append('..')

import os
import planetengine

def diagnostic_01(delete = True):

    observer = planetengine.diagnostic.MS98X_observerscript.build()
    initial = {
        'temperatureField': planetengine.initials.sinusoidal.IC(),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    model1 = planetengine.frame.Frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 16, f = 0.5),
        observer,
        initial
        )

    model1.iterate()

    model1.checkpoint()

    model1.iterate()

    model1.checkpoint()

    model1.load_checkpoint(1)

    initial = {
        'temperatureField': planetengine.initials.load.IC(model1, 'temperatureField'),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    model2 = planetengine.frame.Frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 32, f = 1.),
        observer,
        initial
        )

    model2.checkpoint()

    model2.iterate()

    model2.checkpoint()

    model2.go(2)

    model2.checkpoint()

    model2.reset()

    model2.iterate()

    model2.load_checkpoint(3)

    initial = {
        'temperatureField': planetengine.initials.load.IC(model2, 'temperatureField', loadStep = 1),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    model3 = planetengine.frame.Frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 64, f = 0.5),
        observer,
        initial
        )

    model3.iterate()

    model3.checkpoint()

    model3.iterate()

    model3.checkpoint()

    model3.load_checkpoint(1)

    model1.unarchive()
    model2.unarchive()
    model3.unarchive()

    deepest_path = os.path.join(model3.path, model2.instanceID, model1.instanceID, '00000001', 'stamps.txt')

    assert os.path.isfile(deepest_path)

    model1.archive()
    model2.archive()
    model3.archive()

    if delete:
        os.remove(model1.tarpath)
        os.remove(model2.tarpath)
        os.remove(model3.tarpath)
