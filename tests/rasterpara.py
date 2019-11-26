import planetengine
system = planetengine.systems.isovisc.build(res = 16)
observer = planetengine.observers.standard.build(system)
observer.store()
if planetengine.mpi.rank == 0:
    print(observer.stored)
# raster = planetengine.visualisation.Raster(
#     system.varsOfState['temperature'],
#     system.varsOfState['temperature'],
#     system.varsOfState['temperature'],
#     )
# raster.update()
# if planetengine.mpi.rank == 0:
#     print(raster.data)
#     print(raster.data.shape)
