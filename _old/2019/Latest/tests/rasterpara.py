import planetengine

system = planetengine.systems.isovisc.get(
    res = 16,
    f = 0.5,
    aspect = 2.,
    _initial_temperature = planetengine.initials.sinusoidal.get(freq = 2)
    )
var1 = system.obsVars['temperature']
var2 = planetengine.functions.component.rad(system.obsVars['velocity'])
var3 = planetengine.functions.component.ang(system.obsVars['velocity'])

myraster = planetengine.visualisation.Raster(var1, var2, var3)

myraster.img.save('test.png')

# import planetengine
# system = planetengine.systems.isovisc.get(res = 16)
# observer = planetengine.observers.standard.get(system)
# observer.store()
# if planetengine.mpi.rank == 0:
#     print(observer.stored)
# # raster = planetengine.visualisation.Raster(
# #     system.varsOfState['temperature'],
# #     system.varsOfState['temperature'],
# #     system.varsOfState['temperature'],
# #     )
# # raster.update()
# # if planetengine.mpi.rank == 0:
# #     print(raster.data)
# #     print(raster.data.shape)
