import planetengine
import numpy as np
planetengine.paths.delete_testdir()
outputPath = planetengine.paths.make_testdir()
system = planetengine.systems.arrhenius.build()
# IC = planetengine.initials.sinusoidal.build()
# IC.apply(system.locals.temperatureField)
# system.locals.solver.solve()
# mpi.barrier()
# planetengine.built.save_built(system, 'system', outputPath)
# planetengine.built.save_built(IC, 'IC', outputPath)
# system_load = planetengine.built.load_built('system', outputPath)
# IC_load = planetengine.built.load_built('IC', outputPath)
# IC_load.apply(system_load.locals.temperatureField)
# system_load.locals.solver.solve()
# assert np.allclose(
#     system.locals.velocityField.data,
#     system_load.locals.velocityField.data
#     )
