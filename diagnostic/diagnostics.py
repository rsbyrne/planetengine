import os
import planetengine
import time

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

def diagnostic_01(delete = True):

    planetengine.log("Building model1 initials...")

    initial = {
        'temperatureField': planetengine.initials.sinusoidal.IC(),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    planetengine.log("Building model1...")

    model1 = planetengine.frame.make_frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 16, f = 1., tau = 1e5),
        planetengine.diagnostic.MS98X_observerscript.build(),
        initial
        )

    planetengine.log("Iterating model1...")
    model1.iterate()

    planetengine.log("Checkpointing model1 step 1...")
    model1.checkpoint()

    planetengine.log("Iterating model1...")
    model1.iterate()

    planetengine.log("Checkpointing model1...")
    model1.checkpoint()

    planetengine.log("Loading checkpoint 1 of model1...")
    model1.load_checkpoint(1)

    planetengine.log("Building model2 initials...")
    initial = {
        'temperatureField': planetengine.initials.load.IC(model1, 'temperatureField'),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    planetengine.log("Building model2...")
    model2 = planetengine.frame.make_frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 32, f = 0.5, tau = 4e5),
        planetengine.diagnostic.MS98X_observerscript.build(),
        initial
        )

    planetengine.log("Checkpointing model2 step 0...")
    model2.checkpoint()

    planetengine.log("Iterating model2...")
    model2.iterate()

    planetengine.log("Checkpointing model2 step 1...")
    model2.checkpoint()

    planetengine.log("Iterating model2...")
    model2.iterate()
 
    planetengine.log("Checkpointing model2 step 2...")
    model2.checkpoint()

    planetengine.log("Iterating model2...")
    model2.iterate()

    planetengine.log("Checkpointing model2 step 3...")
    model2.checkpoint()

    planetengine.log("Resetting model2...")
    model2.reset()

    planetengine.log("Iterating model2...")
    model2.iterate()

    planetengine.log("Loading checkpoint 2 of model2...")
    model2.load_checkpoint(2)

    planetengine.log("Building model3 initials...")
    initial = {
        'temperatureField': planetengine.initials.load.IC(model2, 'temperatureField', loadStep = 'max'),
        'materialVar': planetengine.initials.extents.IC((1, planetengine.shapes.trapezoid()))
        }

    planetengine.log("Building model3...")
    model3 = planetengine.frame.make_frame(
        planetengine.diagnostic.MS98X_systemscript.build(res = 64, f = 1., tau = 1e6),
        planetengine.diagnostic.MS98X_observerscript.build(),
        initial
        )

    planetengine.log("Iterating model3...")
    model3.iterate()

    planetengine.log("Checkpointing model3...")
    model3.checkpoint()

    planetengine.log("Iterating model3...")
    model3.iterate()

    planetengine.log("Checkpointing model3...")
    model3.checkpoint()

    planetengine.log("Loading checkpoint 1 of model3...")
    model3.load_checkpoint(1)

    planetengine.log("Unarchiving model1...")
    model1.unarchive()

    planetengine.log("Unarchiving model2...")
    model2.unarchive()

    planetengine.log("Unarchiving model3...")
    model3.unarchive()

    deepest_path = os.path.join(model3.path, model2.instanceID, model1.instanceID, '00000001', 'stamps.txt')
    planetengine.log("Checking deepest path...")
    if rank == 0:
        assert os.path.isfile(deepest_path)

    planetengine.log("Archiving model1...")
    model1.archive()

    planetengine.log("Archiving model2...")
    model2.archive()

    planetengine.log("Archiving model3...")
    model3.archive()

    planetengine.log("Cleaning up...")
    if rank == 0:
        if delete:
            os.remove(model1.tarpath)
            os.remove(model2.tarpath)
            os.remove(model3.tarpath)
            os.remove('diaglog.txt')
    planetengine.message("Diagnostic complete!")
